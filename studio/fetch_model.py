"""Download the speech-to-text model once, if it is not already in the models folder.
Run with:  python -m studio.fetch_model"""
import tarfile
import time
import urllib.request

from . import config, transcribe

URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{config.ASR_MODEL_NAME}.tar.bz2"


def main():
    if transcribe.model_ready():
        print("Speech model already present.")
        return
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if config.ASR_MODEL_TYPE == "faster_whisper":
        from huggingface_hub import snapshot_download
        print("Downloading multilingual Whisper large-v3-turbo (about 1.6 GB)...")
        snapshot_download(repo_id=config.ASR_MODEL_REPO, local_dir=str(config.ASR_MODEL_DIR))
        if not transcribe.model_ready():
            raise RuntimeError("The speech model download finished, but some model files are missing.")
        print("Speech model ready.")
        return
    tmp = config.MODELS_DIR / "speech-model.tar.bz2"
    size = "about 610 MB" if config.ASR_MODEL_TYPE == "whisper" else "480 MB to 1.1 GB"
    print(f"Downloading the speech model ({size})...")
    last = [0.0]

    def progress(blocks, block_size, total):
        now = time.monotonic()
        if total > 0 and (now - last[0] >= 1 or blocks * block_size >= total):
            print(f"\rDownloaded {min(blocks * block_size, total) / total:.0%}", end="\n" if blocks * block_size >= total else "", flush=True)
            last[0] = now

    urllib.request.urlretrieve(URL, tmp, progress)
    with tarfile.open(tmp, "r:bz2") as t:
        for m in t.getmembers():  # only plain files and folders that stay inside the models folder
            if (m.isfile() or m.isdir()) and not m.name.startswith(("/", "..")) and ".." not in m.name.split("/"):
                t.extract(m, config.MODELS_DIR)
    tmp.unlink()
    print("Speech model ready.")


if __name__ == "__main__":
    main()
