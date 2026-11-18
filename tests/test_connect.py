"""YouTube and Instagram setup, sign-in, and posting use platform stand-ins; nothing leaves this machine."""
import json
import os
import shutil
import sys
import tempfile
import time
from urllib.parse import parse_qs, urlparse

DATA = tempfile.mkdtemp(prefix="clippy-connect-")
os.environ.update(PEAKCUT_DATA=DATA, DATABASE_URL="", PEAKCUT_ACCOUNTS="1",
                  PEAKCUT_PUBLIC_URL="https://clips.example.com", PEAKCUT_VERIFY_EMAIL="0",
                  GOOGLE_CLIENT_ID="", GOOGLE_CLIENT_SECRET="", GOOGLE_CLIENT_FILE="",
                  PEAKCUT_IG_APP_ID="", PEAKCUT_IG_APP_SECRET="")
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from studio import accounts, auth, config, ctx, db, jobs, server

db.init()
fails = []


def check(name, got, want=True):
    ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   got {got!r}"))
    if not ok:
        fails.append(name)


def person(email, admin=False):
    user, _ = auth._create(email, email.split("@")[0], password_hash="x")
    if admin:
        with db.engine.begin() as c:
            c.execute(db.users.update().where(db.users.c.id == user.id).values(is_admin=True))
    client = TestClient(server.app, base_url="https://clips.example.com", follow_redirects=False)
    client.cookies.set(auth.COOKIE, auth.start_session(user.id))
    return user, client


owner, admin = person("owner@example.com", admin=True)
user, client = person("user@example.com")
ORIGIN = {"Origin": "https://clips.example.com"}

# Server app setup stays private to administrators, and never returns a secret.
check("no posting apps are configured initially", client.get("/api/status").json()["connect"],
      {"youtube": False, "instagram": False})
check("a regular user cannot read app credentials", client.get("/api/apps").status_code, 404)
check("a regular user cannot change app credentials", client.put("/api/apps", json={"platform": "youtube"}, headers=ORIGIN).status_code, 404)
check("cross-site changes are refused", admin.put("/api/apps", json={"platform": "youtube", "client_id": "google-client-123", "client_secret": "secret"},
                                                        headers={"Origin": "https://other.example"}).status_code, 403)
for platform, client_id in (("youtube", "google-client-123.apps"), ("instagram", "1234567890")):
    r = admin.put("/api/apps", json={"platform": platform, "client_id": client_id,
                                     "client_secret": f"{platform}-secret-value"}, headers=ORIGIN)
    check(f"{platform} app can be saved", (r.status_code, r.json()[platform]["ready"]), (200, True))
check("app secrets are not returned", "secret-value" not in json.dumps(admin.get("/api/apps").json()))
check("app callback address is shown", admin.get("/api/apps").json()["instagram"]["redirect"],
      "https://clips.example.com/oauth/instagram/callback")
check("users can connect after server setup", client.get("/api/status").json()["connect"],
      {"youtube": True, "instagram": True})


class Response:
    def __init__(self, code, data=None, headers=None):
        self.status_code, self._data, self.headers = code, data, headers or {}
        self.text = json.dumps(data)

    def json(self):
        return self._data


calls = []


def post(url, data=None, json=None, headers=None, params=None, timeout=None, content=None):
    body = data if data is not None else json
    calls.append(("POST", url, body, headers or {}))
    if url == "https://oauth2.googleapis.com/token":
        return Response(200, {"access_token": "yt-access", "refresh_token": "yt-refresh", "expires_in": 3600})
    if url == "https://api.instagram.com/oauth/access_token":
        return Response(200, {"data": [{"access_token": "ig-short", "user_id": "17841",
                                         "permissions": "instagram_business_basic,instagram_business_content_publish"}]})
    if url.endswith("/17841/media"):
        return Response(200, {"id": "container1"})
    if url.endswith("/17841/media_publish"):
        return Response(200, {"id": "media1"})
    if url.endswith("/youtube/v3/videos"):
        return Response(200, {}, {"Location": "https://upload.example/youtube/1"})
    return Response(404, {})


def get(url, params=None, headers=None, timeout=None):
    calls.append(("GET", url, params, headers or {}))
    if url.endswith("/youtube/v3/channels"):
        return Response(200, {"items": [{"id": "UC123", "snippet": {"title": "My Channel"}}]})
    if url == "https://graph.instagram.com/access_token":
        return Response(200, {"access_token": "ig-long", "expires_in": 5183944})
    if url.endswith("/v27.0/me"):
        return Response(200, {"user_id": "17841", "username": "clipper", "account_type": "MEDIA_CREATOR"})
    if url.endswith("/container1"):
        return Response(200, {"status_code": "FINISHED"})
    if url.endswith("/media1"):
        return Response(200, {"permalink": "https://www.instagram.com/reel/abc/"})
    return Response(404, {})


def put(url, content=None, headers=None, timeout=None):
    calls.append(("PUT", url, len(content or b""), headers or {}))
    return Response(201, {"id": "video1"})


accounts.httpx.post, accounts.httpx.get, accounts.httpx.put = post, get, put
accounts.time.sleep = lambda _s: None


def connect(platform, code="code"):
    start = client.get(f"/oauth/{platform}/start")
    query = parse_qs(urlparse(start.headers["location"]).query)
    state = query["state"][0]
    finish = client.get(f"/oauth/{platform}/callback", params={"code": code, "state": state})
    return urlparse(start.headers["location"]), query, finish


google_url, google, google_back = connect("youtube")
check("YouTube uses Google's sign-in and upload permission",
      (google_url.netloc, "youtube.upload" in google["scope"][0]), ("accounts.google.com", True))
check("YouTube sign-in returns to Connected apps", "connected=youtube" in google_back.headers["location"])
instagram_url, instagram, instagram_back = connect("instagram", "ig-code#_")
check("Instagram uses its sign-in and publishing permission",
      (instagram_url.netloc, instagram["client_id"][0], "instagram_business_content_publish" in instagram["scope"][0]),
      ("www.instagram.com", "1234567890", True))
check("Instagram sign-in returns to Connected apps", "connected=instagram" in instagram_back.headers["location"])
mine = {a["platform"]: a for a in client.get("/api/accounts").json()}
check("connected account names are shown", (mine["youtube"]["name"], mine["instagram"]["name"]), ("My Channel", "@clipper"))
check("access and refresh tokens never reach the page", all(token not in client.get("/api/accounts").text
      for token in ("yt-access", "yt-refresh", "ig-long")))
check("another user cannot see these accounts", admin.get("/api/accounts").json(), [])

# YouTube's resumable upload path.
video = config.user_dir(user.id) / "tmp-test.mp4"
video.parent.mkdir(parents=True, exist_ok=True)
video.write_bytes(b"video-bytes")
with ctx.as_user(user.id):
    yt = accounts.get(mine["youtube"]["id"])
    youtube_id, youtube_url = accounts.youtube_upload(yt, video, "A clip", "Description", ["gaming"], "unlisted")
check("YouTube uploads a clip and returns a Shorts link", (youtube_id, youtube_url),
      ("video1", "https://www.youtube.com/shorts/video1"))
check("YouTube sends the expected Shorts metadata", any(c[0] == "POST" and c[1].endswith("/youtube/v3/videos")
      and c[2]["snippet"]["title"] == "A clip" for c in calls))

# Instagram's signed public URL is reachable without a Clippy session and scoped to this one clip.
job_dir = config.user_dir(user.id) / "jobs" / "job-12345678"
(job_dir / "clips").mkdir(parents=True)
(job_dir / "job.json").write_text(json.dumps({"id": "job-12345678", "user": user.id, "dir": str(job_dir),
    "clips": [], "status": "done", "creator": None, "created": time.time(), "options": {}, "source": {"type": "file"}}), encoding="utf-8")
(job_dir / "clips" / "clip01.mp4").write_bytes(b"sample-mp4")
jobs.load_user(user.id)
anon = TestClient(server.app, base_url="https://clips.example.com")
with ctx.as_user(user.id):
    clip_url = accounts.clip_link("job-12345678", "clip01.mp4")
    ig = accounts.get(mine["instagram"]["id"])
    media_id, permalink = accounts.instagram_upload(ig, job_dir / "clips" / "clip01.mp4", "Clip caption", "job-12345678")
clip_path = urlparse(clip_url).path
check("signed Instagram video URL serves the clip without sign-in",
      (anon.get(clip_path).status_code, anon.get(clip_path).content), (200, b"sample-mp4"))
check("changed signed video URL is rejected", anon.get(clip_path.replace("/pub/", "/pub/x", 1)).status_code, 404)
ig_start = next(c for c in calls if c[0] == "POST" and c[1].endswith("/17841/media"))
check("Instagram starts a Reel using the signed video address",
      (ig_start[2]["media_type"], ig_start[2]["video_url"].startswith("https://clips.example.com/pub/")), ("REELS", True))
check("Instagram uses the current pinned Graph API version", "/v27.0/" in ig_start[1])
check("Instagram publishes the Reel and returns its link", (media_id, permalink),
      ("media1", "https://www.instagram.com/reel/abc/"))

print("ALL PASSED" if not fails else f"{len(fails)} failed")
db.engine.dispose()
shutil.rmtree(DATA, ignore_errors=True)
sys.exit(1 if fails else 0)
