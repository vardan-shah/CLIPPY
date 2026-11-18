#!/bin/zsh
set -e
cd -- "$(dirname -- "$0")"

PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo "Python 3 is required. Install Python 3.10 to 3.13, then run this launcher again."
  read "?Press Return to close. "
  exit 1
fi
if [[ -x /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg ]]; then
  PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH"
  export PATH
fi
FFMPEG_BIN="$(command -v ffmpeg 2>/dev/null || true)"
if [[ -z "$FFMPEG_BIN" ]]; then
  echo "FFmpeg is required. On a Mac with Homebrew, run: brew install ffmpeg-full"
  read "?Press Return to close. "
  exit 1
fi
if ! "$FFMPEG_BIN" -hide_banner -filters 2>/dev/null | awk '$2 == "ass" { found=1 } END { exit !found }'; then
  echo "This FFmpeg build cannot render Clippy's captions. On a Mac with Homebrew, run: brew install ffmpeg-full"
  read "?Press Return to close. "
  exit 1
fi

if [[ -x .venv/bin/python ]] && ! .venv/bin/python -c 'import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)' >/dev/null 2>&1; then
  echo "Rebuilding Clippy's local Python environment with $PYTHON."
  rm -rf .venv
fi
if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON" -m venv .venv
fi
if ! .venv/bin/python -c 'import faster_whisper, fastapi, httpx, numpy, PIL, sherpa_onnx, soundfile, sqlalchemy, uvicorn, yt_dlp' >/dev/null 2>&1; then
  echo "Installing Clippy's Python packages. This may take a few minutes."
  .venv/bin/python -m pip install -r requirements.txt --index-url https://pypi.org/simple
fi

if ! .venv/bin/python -c 'from studio.transcribe import model_ready; raise SystemExit(0 if model_ready() else 1)' >/dev/null 2>&1; then
  echo "Downloading Clippy's multilingual Whisper Turbo model (about 1.6 GB) for English, Hindi and Hinglish."
  .venv/bin/python -m studio.fetch_model
fi

APP_URL="$(.venv/bin/python -c 'from studio import config; print(f"http://127.0.0.1:{config.PORT}")')"
(
  for i in {1..60}; do
    if curl -fsS "$APP_URL/healthz" >/dev/null 2>&1; then
      open "$APP_URL/app"
      exit 0
    fi
    sleep 1
  done
) &
exec .venv/bin/python -m studio.server
