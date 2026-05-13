#!/usr/bin/env python
"""
Run the Flask server for the Maps Scraper API.
"""

import os
from pathlib import Path

from src.core.api.app import app

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR = BASE_DIR / "models" / "distilbert_finetuned"
DEFAULT_DRIVE_URL = "https://drive.google.com/drive/folders/1DlBeK5INJGk12s5821FIIZeVVeAEsYxL?usp=drive_link"

MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_DIR))).resolve()


def download_model(model_dir: Path, download_url: str) -> None:
    if model_dir.exists():
        return

    print(f"Downloading model from Google Drive to {model_dir}...")

    try:
        gdown = __import__("gdown")
    except ImportError as exc:
        raise ImportError(
            "The Python package 'gdown' is required to download the model from Google Drive. "
            "Install it with 'pip install gdown' or set MODEL_PATH to a local model folder."
        ) from exc

    model_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        gdown.download_folder(download_url, output=str(model_dir), quiet=False)
    except Exception as exc:
        raise RuntimeError(
            "Failed to download the model from Google Drive. "
            "Ensure the folder is shared as 'Anyone with the link' or set MODEL_PATH to a local model directory. "
            "If you are using a private Drive link, set MODEL_DOWNLOAD_URL to a publicly accessible download URL instead."
        ) from exc

    if not model_dir.exists():
        raise FileNotFoundError(f"Model download failed: {model_dir} does not exist after download.")


# Ensure the model is available before starting the Flask app.
download_url = os.getenv("MODEL_DOWNLOAD_URL", DEFAULT_DRIVE_URL)
download_model(MODEL_PATH, download_url)

MODEL_PATH_STR = MODEL_PATH.as_posix()
os.environ["MODEL_PATH"] = MODEL_PATH_STR
app.config["MODEL_PATH"] = MODEL_PATH_STR

PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

print(f"Starting Flask server on http://{HOST}:{PORT}")
print("API endpoints:")
print("  POST   /scrape          - Start scraping job")
print("  GET    /status/<job_id> - Get job status")
print("  GET    /data            - List processed files")
print("  GET    /export/<file>   - Download file")
print("  GET    /health          - Health check")
print("  [MODEL] Path configured:", MODEL_PATH_STR)

app.run(debug=DEBUG, host=HOST, port=PORT)
