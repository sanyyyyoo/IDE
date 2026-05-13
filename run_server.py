#!/usr/bin/env python
"""
Run the Flask server for the Maps Scraper API.
"""

import os
from src.core.api.app import app

# ✅ Define the absolute model path once
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "distilbert_finetuned")

# Normalize Windows slashes → forward slashes
MODEL_PATH = MODEL_PATH.replace("\\", "/")

# Print model path info on startup
print("Starting Flask server on http://localhost:8000")
print("API endpoints:")
print("  POST   /scrape          - Start scraping job")
print("  GET    /status/<job_id> - Get job status")
print("  GET    /data            - List processed files")
print("  GET    /export/<file>   - Download file")
print("  GET    /health          - Health check")
import os
os.environ["MODEL_PATH"] = "C:/Users/PMCC/Desktop/IDE/models/distilbert_finetuned"
print("  [MODEL] Path configured:", os.environ["MODEL_PATH"])


# Make model path accessible to the app
app.config["MODEL_PATH"] = MODEL_PATH

app.run(debug=True, host="0.0.0.0", port=8000)
