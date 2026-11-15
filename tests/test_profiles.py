"""YouTube profile detection works for channel links and video links without contacting YouTube."""
import os
import shutil
import sys
import tempfile

os.environ["PEAKCUT_DATA"] = tempfile.mkdtemp(prefix="clippy-profiles-")
os.environ["DATABASE_URL"] = ""
sys.path.insert(0, ".")
from studio import profiles  # noqa: E402

failed = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        failed.append(name)


check(
    "meta tags are read when attributes are reordered and single-quoted",
    profiles._meta(
        "<meta content='Makers &amp; Friends' name='og:title'>",
        "og:title",
    ) == "Makers & Friends",
)

profiles._cache.clear()
profiles._get = lambda _url: (
    "text/html",
    b"<meta content='Studio Name' property='og:title'><meta content='https://yt3.googleusercontent.com/pic' property='og:image'>",
)
channel = profiles.fetch("https://www.youtube.com/@studio/videos")
check("YouTube channel aliases resolve to the channel name", channel["name"] == "Studio Name")
check("channel tabs are normalized to a channel URL", channel["channel_url"] == "https://www.youtube.com/@studio")

profiles._cache.clear()
profiles._ydl_info = lambda url: {
    "channel": "Video Creator",
    "channel_url": "https://www.youtube.com/@video-creator",
}
video = profiles.fetch("https://www.youtube.com/live/Kush1FqnhbU?si=example")
check("YouTube live archive resolves to its creator", video["name"] == "Video Creator")
check("video links resolve to a reusable creator channel", video["channel_url"] == "https://www.youtube.com/@video-creator")

shutil.rmtree(os.environ["PEAKCUT_DATA"], ignore_errors=True)
sys.exit(1 if failed else 0)
