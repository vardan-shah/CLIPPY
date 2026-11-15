# CLIPPY

Turn long videos and live streams into captioned vertical clips, ready to post. Free and open source: run it on
your own computer. Local Ollama is the default AI, so clipping does not require API credits or a paid AI account.

Clippy is a customized, local-first version of PeakCut. The upstream MIT license is kept in [LICENSE](LICENSE).

Paste a YouTube, Twitch or Kick link (or upload a file) and Clippy finds the moments worth clipping, cuts them to
9:16, adds word-by-word captions and a hook, and can post them to your connected accounts. It can also record a
creator's live stream and clip the highlights while the stream is still running.

## What it does

- **Clips from any video.** Transcribes the audio, asks an AI which moments would hold a stranger's attention, and
  renders each one with captions in one of three styles.
- **Batch work.** Add up to five videos at once; the machine's load check slows new work when it is busy.
- **Live clipping.** Records a stream into a rolling buffer and clips as it happens, using loudness, chat activity
  and the transcript.
- **Workspaces per creator.** Channels, clip settings, posting rules and an activity log for each creator you clip.
- **Posting.** Queue or auto-post finished clips to YouTube Shorts and Instagram Reels, with spacing and daily caps.
- **No sign-in on your own computer.** It opens straight into the dashboard. On a shared server, switch accounts on
  (`PEAKCUT_ACCOUNTS=1`) for email or Google sign-in and an admin dashboard.
- **Local AI by default.** Ollama runs on your computer; Clippy does not send video or transcript text to an AI
  provider in this mode. Cloud AI services are optional and may charge you.
- **No-model fallback.** If Ollama is unavailable, Clippy can still find short speech moments from audio peaks.
  It labels them as audio-only picks and gives each a score from its measured sound signal.

## Quick start

You need Python 3.10–3.13 and FFmpeg with the `ass` subtitle filter (libass). On macOS with Homebrew, install the
full build with `brew install ffmpeg-full`; Clippy checks for this before it starts.

On macOS, double-click [`start-clippy.command`](start-clippy.command). It checks for Python and FFmpeg, installs
the Python packages in a local virtual environment, downloads the speech model if needed, starts the server and
opens Clippy in your browser.

Or start it manually from the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt --index-url https://pypi.org/simple
```

Download the multilingual Whisper large-v3-turbo speech model once (about 1.6 GB) and start the server. It detects
the spoken language locally, including English, Hindi and mixed Hindi-English:

```bash
python -m studio.fetch_model
```

For AI clip selection without API credits, install [Ollama](https://ollama.com/) and download the default model:

```bash
ollama pull qwen2.5:7b
```

If Ollama is not running or you do not install it, Clippy automatically uses its no-model loudness picker.
Video transcription and rendering run locally either way. Local processing still uses your computer's disk space,
memory and electricity.

```bash
python -m studio.server
```

Open http://127.0.0.1:8765/app. There is no sign-in on your own computer.

**Keep the server running while using Clippy.** Do not open `web/index.html` from Finder: a `file://` page cannot
reach the local API, which prevents navigation, channel lookup and video link previews from working. The page
now explains this if opened directly.

Clippy works with both regular YouTube videos and live streams. Paste a video link on Home or All videos to clip
it; add a creator when you want a saved workspace or automatic live recording.

## Connect YouTube or Instagram

Open **Settings → Connected apps**. The first time, the server owner registers an app with each platform, copies
the callback address Clippy shows, and saves the app ID and secret there. Clippy then sends each creator to the
platform's own sign-in page; it does not ask for their password.

- **YouTube:** create a Google Cloud web OAuth client, enable **YouTube Data API v3**, and register the callback
  shown in Clippy. Add your Google account as a test user if the consent screen is still in testing.
- **Instagram:** create a Meta app with **Instagram API with Instagram Login**, add the callback shown in Clippy,
  and use a Creator or Business account. Meta must be able to fetch the finished video from a public HTTPS address;
  for a local install, set `PEAKCUT_PUBLIC_URL` to an HTTPS tunnel or domain before connecting.

You can also provide Google credentials with `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`, and Instagram app
credentials with `PEAKCUT_IG_APP_ID` and `PEAKCUT_IG_APP_SECRET`. The app credentials and connected account tokens
are stored in the ignored `data` folder, never in the repository.

## Choose your AI

Clippy needs a chat model that can return JSON. The default is Ollama at `http://127.0.0.1:11434`; install it
and pull `qwen2.5:7b` to keep AI selection local. In **Settings, AI**, choose Ollama and enter the
model name if you want to use another local model. No API key is needed.

You can instead choose a cloud provider in **Settings, AI**, press **Find models**, choose a model and **Save and
test**. Those services can charge for use; Clippy does not include credits.

If you prefer a file (or run a server), the same three things can go in `.env`. What is saved in the dashboard wins:

```ini
PEAKCUT_AI_PROVIDER=ollama
PEAKCUT_AI_MODELS=qwen2.5:7b
```

| `PEAKCUT_AI_PROVIDER` | Service | Where to get a key |
|---|---|---|
| `gemini` | Google Gemini (may charge) | https://aistudio.google.com/apikey |
| `openai` | OpenAI | https://platform.openai.com/api-keys |
| `xai` | Grok (xAI) | https://console.x.ai |
| `groq` | Groq | https://console.groq.com/keys |
| `openrouter` | OpenRouter (many models, one key) | https://openrouter.ai/keys |
| `anthropic` | Claude | https://console.anthropic.com |
| `ollama` | A model on your own machine, no key or API credits | https://ollama.com |
| `custom` | Any OpenAI-compatible address: also set `PEAKCUT_AI_BASE_URL` | |

- `PEAKCUT_AI_MODELS` is the model id exactly as the service names it. Model names change often, so check the
  service's current list. Several ids separated by commas are tried in order, which gives you a fallback.
- A fast model is the right choice. A one-hour video is read in about four requests.
- Cloud AI use is billed by the provider. The **AI usage** page shows how many requests and tokens each video took.
- Speech to text does not use the AI service. It runs on your own machine, so audio never leaves it.

## Settings

Everything is set through environment variables, normally in a `.env` file next to this README.
[`.env.example`](.env.example) lists every setting with a short explanation. The ones that matter first:

| Setting | What it is for |
|---|---|
| `PEAKCUT_AI_PROVIDER`, `PEAKCUT_AI_MODELS`, `PEAKCUT_AI_KEY` | The AI that picks clips and writes titles (or set it in the dashboard) |
| `PEAKCUT_ACCOUNTS` | `1` makes everyone sign in. Use it on any server other people can reach |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Optional: Sign in with Google, and connecting YouTube |
| `PEAKCUT_SMTP_*`, `PEAKCUT_MAIL_FROM` | Optional: confirmation and password emails |
| `PEAKCUT_DATA` | Where videos, clips and the database are kept (default `./data`) |

`.env`, the `secrets/` folder and all user data are ignored by git. Keep keys there, never in the code.

## Admins

This only matters with accounts switched on (`PEAKCUT_ACCOUNTS=1`); without them you are the owner and can do
everything. An account is an admin only when the database says so. No email address is special in the code and no web request
can change a role. Do it on the machine that runs Clippy:

```bash
python -m studio.admin grant you@example.com
```

`revoke` and `list` work the same way. The admin dashboard is at `/admin` and answers "not found" to everyone else.

## How it is built

| Part | What it is |
|---|---|
| `studio/` | The server: FastAPI, the clip pipeline, live recording, accounts |
| `studio/ai.py` | The only file that talks to an AI service. Add a provider here |
| `web/` | The pages: landing, sign-in, the app, the admin dashboard (plain HTML, CSS and JavaScript, no build step) |
| `tests/` | Tests that run against a throwaway copy of the app |
| `deploy/`, `Dockerfile`, `docker-compose.yml` | One-server deployment with PostgreSQL and automatic HTTPS |

Video work is done with `ffmpeg` and `yt-dlp`. Speech is transcribed with `sherpa-onnx` and the Parakeet model.
Data is kept per user: accounts in the database (SQLite on your own computer, PostgreSQL on a server), videos and
clips in each user's own folder. [AGENTS.md](AGENTS.md) is a short map of the code for contributors and AI coding
assistants.

## Deploy

[DEPLOY.md](DEPLOY.md) walks through a single server with Docker: the app, PostgreSQL, and Caddy for HTTPS.

```bash
docker compose up -d --build
```

## How it behaves under load

- The page asks the server one small question every few seconds. When nothing has changed, the answer comes
  straight from memory.
- Each person's videos wait in their own line and the lines take turns, so one person cannot hold everyone up.
- The server measures its own processor, memory and disk every second. Extra videos and recordings start only
  while there is room, wait briefly when it is nearly full, and continue the moment it frees up.
- Uploads, video length, storage per account and request sizes all have limits, set in `.env`.

## Tests

```bash
python tests/run.py
```

This starts a copy of the app on a spare port with an empty temporary data folder, runs the permission, abuse and
queue tests against it, then removes it. It needs no keys and never touches real data.

## Security

- With sign-in off, Clippy listens on this computer only (`127.0.0.1`), refuses changes sent by other websites,
  and only answers to its own address. Do not expose it to the internet that way: turn accounts on.
- Passwords are stored only as salted scrypt hashes. Sessions are random tokens stored hashed; cookies are HTTP-only.
- Every route works out who is asking from the session, never from the request, so users only reach their own data.
- Only known video sites are fetched, and text from videos is treated as data when it is shown to the AI.
- Found a problem? Please report it privately through the repository's security advisories instead of opening a
  public issue.

## Using it responsibly

Clip videos you made, or have permission to use. You are responsible for the rights to what you download, clip and
post, and for following the terms of the sites you fetch from and post to.

## Licence

[MIT](LICENSE). Caption fonts in `studio/fonts/` (Anton, Archivo Black, Poppins) are under the SIL Open Font
License; the licence texts are in the same folder.
