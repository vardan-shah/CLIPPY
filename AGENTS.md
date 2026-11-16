# Working on Clippy

A short map for contributors and AI coding assistants.

## Run and test

- Run: `python -m studio.server` (settings from `.env`; see `.env.example`). Needs Python 3.10+ and `ffmpeg`.
- Speech model, once: `python -m studio.fetch_model`.
- Tests: `python tests/run.py`. It starts a throwaway copy on a spare port with an empty data folder. Run it
  before and after any change to `studio/`. No keys needed.
- To try a risky change by hand without touching real data:
  `PEAKCUT_DATA=<temp folder> PEAKCUT_PORT=8766 python -m studio.server`.

## Where things are

| File | What it does |
|---|---|
| `studio/server.py` | Every web route, and the gate that runs before each request (who is asking, limits, headers) |
| `studio/config.py` | Every setting, read from environment variables |
| `studio/ai.py` | The only code that talks to an AI service, and the AI settings saved from the dashboard (`ai.json` in the data folder) |
| `studio/brain.py` | The prompts: finding clips, live judging, hooks and titles, caption fixes |
| `studio/usage.py` | The record of AI calls and tokens shown on the AI usage page |
| `studio/jobs.py` | The video pipeline and the fair queue |
| `studio/live.py` | Live recording and clipping |
| `studio/transcribe.py`, `studio/asr_worker.py` | Speech to text, here or on a second machine |
| `studio/render.py` | Cutting, layouts and captions (ffmpeg and Pillow) |
| `studio/media.py` | Downloading (yt-dlp), probing, audio |
| `studio/auth.py`, `studio/account.py`, `studio/admin.py` | Sign-in, deleting things, the admin dashboard |
| `studio/db.py` | Database tables (SQLAlchemy core; SQLite or PostgreSQL) |
| `web/index.html` | The whole signed-in app, one file, no build step |

## Rules worth knowing

- **Sign-in is off by default** (`config.ACCOUNTS`): every request then belongs to one built-in owner
  (`auth.local_user()`). With `PEAKCUT_ACCOUNTS=1` it is a normal multi-user site. Both paths are tested.
- **Who is asking** always comes from the session (`ctx.uid()`), never from the request body. Background threads
  set it themselves with `ctx.as_user(...)`.
- **Anything that changes what a user sees must call `ctx.bump()`**. The page polls `/api/sync`, which answers
  from memory when that user's counter has not moved.
- **Text from videos is untrusted**: it goes into prompts through `brain._safe` and out through `brain._text`.
- **Adding an AI provider**: add a row to `PROVIDERS` in `studio/ai.py`. If it speaks the OpenAI chat format that
  is all; otherwise add one function that returns `(parsed JSON, tokens in, tokens out)`.
- **Clips are rendered in a short temporary folder** and moved into place (`render.render_clip`): ffmpeg's caption
  step cannot open paths longer than 260 characters on Windows.
- **Secrets** are read from the environment or from files named by `*_FILE` settings. Never write a key, a real
  address or a personal path into a tracked file.
- **Pages** are plain HTML, CSS and JavaScript. Keep the existing palette, no shadows, and hover states that
  change colour only.
- Comments and messages are written in plain language for people who do not program. Keep that tone.

## Ponytail: minimal, correct changes

Apply the Ponytail ruleset (MIT, DietrichGebert/ponytail) to coding work in this repository.

- Read the relevant implementation and its callers before changing code. Prefer the smallest complete change that fits the existing architecture.
- First reuse existing helpers, patterns, standard-library features, platform capabilities and installed dependencies. Do not add dependencies, wrappers, abstractions, configuration or speculative options without a concrete need.
- Remove genuinely redundant code instead of layering another helper on top. Do not equate short code with correct code: preserve readability and edge-case behavior.
- Never remove input validation, authorization, security controls, accessibility, meaningful error handling, data-loss safeguards or user-requested functionality to reduce line count.
- For non-trivial new logic (branches, loops, parsing, money, security, or a new script), add a focused test. Keep the existing test conventions.
- For bug fixes, inspect all callers and fix the shared root cause where possible. Update affected tests and fixtures.
- When reviewing, inspect related code beyond the diff. Report concrete findings with file/line, impact, evidence and a minimal fix. Do not label code "AI-generated" based on style or heuristics.
- Do not automatically delete code based on speculative cleanup findings. Make changes only when behavior is understood and tests or other evidence support the change.
- Before finishing, run `python tests/run.py` for changes affecting `studio/`; run relevant checks for other changes. State exactly what was and was not tested, and identify remaining risks.
- Keep changes within the requested scope. Prefer deletion when it demonstrably preserves behavior.

Ponytail reference: https://github.com/DietrichGebert/ponytail
