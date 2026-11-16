"""Regression tests for strict booleans, finite numeric inputs, and single-use email links."""
import os
import shutil
import sys
import tempfile

DATA = tempfile.mkdtemp(prefix="clippy-validation-")
os.environ.update(PEAKCUT_DATA=DATA, DATABASE_URL="", PEAKCUT_ACCOUNTS="1", PEAKCUT_VERIFY_EMAIL="1")
sys.path.insert(0, ".")

from studio import accounts, auth, creators, ctx, db, jobs

db.init()
fails = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


user, _ = auth._create("validation@example.com", "Validation", password_hash="x")
with ctx.as_user(user.id):
    for field in ("auto_watch", "autopost", "ai_only_on_spike"):
        check(f"creator {field}=false remains false", creators._clean({field: False})[field] is False)
        check(f"creator {field}=true remains true", creators._clean({field: True})[field] is True)
        try:
            creators._clean({field: "false"})
            ok = False
        except ValueError:
            ok = True
        check(f"creator {field} rejects string booleans", ok)

    for field in ("paused", "tour_done"):
        check(f"account setting {field}=false remains false",
              accounts.save_settings({field: False})[field] is False)
        check(f"account setting {field}=true remains true",
              accounts.save_settings({field: True})[field] is True)
        try:
            accounts.save_settings({field: "false"})
            ok = False
        except ValueError:
            ok = True
        check(f"account setting {field} rejects string booleans", ok)

for value in ("NaN", "Infinity", "-Infinity", 1e309):
    for field in ("max_clips", "range_end"):
        try:
            jobs.clean_options({field: value})
            ok = False
        except ValueError:
            ok = True
        check(f"job option {field} rejects {value}", ok)
    for field in ("max_clips", "rate_per_1k"):
        try:
            creators._clean({field: value})
            ok = False
        except ValueError:
            ok = True
        check(f"creator setting {field} rejects {value}", ok)

token = auth._make_link(user.id, "verify", 300)
check("a valid email link is accepted once", auth._use_link(token, "verify") == user.id)
try:
    auth._use_link(token, "verify")
    ok = False
except auth.AuthError:
    ok = True
check("a consumed email link cannot be reused", ok)

db.engine.dispose()
shutil.rmtree(DATA, ignore_errors=True)
print("ALL PASSED" if not fails else f"{len(fails)} failed")
sys.exit(1 if fails else 0)
