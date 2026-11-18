"""Live links from the composer should use the creator's existing recorder."""
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

DATA = Path(tempfile.mkdtemp(prefix="clippy-live-intake-"))
os.environ["PEAKCUT_DATA"] = str(DATA)
os.environ["DATABASE_URL"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import alerts, creators, ctx, jobs, live, media, server  # noqa: E402

failed = []


def check(name, fn):
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {name}: {e}")
        failed.append(name)
    else:
        print(f"PASS {name}")


url = "https://www.youtube.com/watch?v=Kush1FqnhbU"
creator = {"id": "creator1", "name": "Streamer", "channel": "https://youtube.com/@streamer"}
job = {"id": "20261118-162457-e5b9d5b262", "kind": "live", "creator": "creator1", "user": "u_local",
       "status": "live", "stage": "Recording", "source": {"type": "live", "url": url},
       "options": {}, "clips": [], "ai": {}}
media._PREVIEWS[url] = {"is_live": True, "title": "Stream", "uploader": "Streamer", "duration": 0}


def invoke(active, creator_id="creator1", active_mine=()):
    with (patch.object(server, "_need_verified"), patch.object(server, "_quota"),
          patch.object(server, "_throttle"), patch.object(creators, "get", return_value=creator),
          patch.object(live, "active_for", return_value=active),
          patch.object(live, "active_mine", return_value=list(active_mine))):
        with ctx.as_user("u_local"):
            return server.create_from_link({"url": url, "creator": creator_id})


def reuses_active():
    active = type("Active", (), {"job": job})()
    with patch.object(server.jobs, "create", side_effect=AssertionError("queued as a normal video")):
        result = invoke(active)
    assert result["id"] == job["id"] and result["kind"] == "live"


def starts_live_recording():
    with patch.object(live, "start_session", return_value=job) as start:
        result = invoke(None)
    start.assert_called_once_with(creator, url)
    assert result["kind"] == "live"


def refreshes_stale_live_preview():
    media._PREVIEWS[url] = {"is_live": False, "title": "Upcoming stream", "uploader": "Streamer", "duration": 0}
    active = type("Active", (), {"job": job})()
    with patch.object(media, "info", return_value={"is_live": True, "kind": "video", "title": "Stream",
                                                     "uploader": "Streamer", "duration": 0, "thumbnail": ""}) as info:
        result = invoke(active)
    info.assert_called_once_with(url)
    assert result["id"] == job["id"] and media._PREVIEWS[url]["is_live"]


def reuses_matching_recording_without_creator_selection():
    active_job = dict(job, uploader="Streamer")
    active = type("Active", (), {"job": active_job})()
    result = invoke(None, "", [active])
    assert result["id"] == job["id"] and result["kind"] == "live"


def requires_creator():
    try:
        invoke(None, "")
    except HTTPException as e:
        assert e.status_code == 400 and "creator workspace" in e.detail
    else:
        raise AssertionError("live link was accepted without a creator workspace")


def checks_final_window_after_stop():
    directory = DATA / "stopped-session"
    directory.mkdir()
    recording = live.Session({"id": "stopped", "dir": str(directory), "creator": "creator1", "title": "Stream",
                              "uploader": "Streamer", "clips": [], "source": {"name": "Streamer live"},
                              "ai": {}}, {})
    recording.user_stopped = True
    recording.ended = False
    recording.t_done = 30
    recording._scan_segments = lambda: None
    recording._transcribe_step = lambda: False
    recording._manual_step = recording._watch_spikes = recording._publish = lambda: None
    calls = []
    recording._ask_ai = lambda *args: calls.append(args)
    # Stop may be pressed before the ingest thread has noticed FFmpeg exit.
    with (patch.object(live.time, "sleep", side_effect=lambda _: setattr(recording, "ended", True)),
          patch.object(jobs, "save"), patch.object(creators, "log"), patch.object(alerts, "notify")):
        recording._analyze()
    assert calls == [()]


def accepts_twitch_and_kick():
    assert media.site_allowed("https://www.twitch.tv/streamer")
    assert live.normalize("twitch.tv/streamer") == "https://twitch.tv/streamer"
    assert media.site_allowed("https://kick.com/streamer")
    assert live.normalize("kick.com/streamer") == "https://kick.com/streamer"


def publishes_live_progress():
    directory = DATA / "publish-session"
    directory.mkdir()
    recording = live.Session({"id": "publish", "user": "u_local", "dir": str(directory), "creator": "creator1",
                              "title": "Stream", "uploader": "Streamer", "clips": [],
                              "source": {"name": "Streamer live"}, "ai": {}}, {})
    recording.words = [{"w": word, "s": i * 0.5, "e": i * 0.5 + 0.4} for i, word in enumerate(
        "we found the game and now it is working live for every viewer".split())]
    recording.samples = 20 * live.SR
    recording.t_done = 20
    recording.db = [-25.0] * 20
    with ctx.as_user("u_local"):
        recording._publish()
    assert recording.job["live"]["elapsed"] == 20
    assert recording.job["live"]["words"] == len(recording.words)


check("pasted live link reuses the creator's active recording", reuses_active)
check("pasted live link starts the creator recorder", starts_live_recording)
check("stale preview refreshes when a scheduled stream goes live", refreshes_stale_live_preview)
check("all videos reuses a matching live recording without creator selection", reuses_matching_recording_without_creator_selection)
check("live link without a creator explains how to proceed", requires_creator)
check("stopping a recording makes a final AI check", checks_final_window_after_stop)
check("Twitch and Kick live channel links are accepted", accepts_twitch_and_kick)
check("live status publishes transcript and recording progress", publishes_live_progress)
shutil.rmtree(DATA, ignore_errors=True)
sys.exit(1 if failed else 0)
