# Maps Scraper - Flask Backend

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Flask Backend

```bash
python run_server.py
```

Or directly:
```bash
python -m src.core.api.app
```

The server will start on `http://localhost:8000`

### 3. Open the Frontend

Open `frontend/index.html` in your browser, or serve it with a simple HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

## API Endpoints

- `POST /scrape` - Start a scraping job
  ```json
  {
    "city": "Mumbai",
    "categories": ["Grocery store", "Pharmacy"],
    "output_filename": "optional_custom_name.xlsx"
  }
  ```

- `GET /status/<job_id>` - Get job status
- `GET /data` - List all processed files
- `GET /export/<filename>` - Download a file
- `GET /health` - Health check

## Project Structure

```
.
├── src/
│   └── core/
│       ├── api/
│       │   └── app.py          # Flask application
│       ├── ml/                 # ML models and classifiers
│       └── scraping/           # Scraping logic
├── frontend/
│   ├── index.html              # Main frontend
│   ├── styles.css              # Styling
│   └── app.js                 # Frontend logic
├── models/                     # Trained models
├── data/
│   └── processed/              # Output files
└── run_server.py              # Server startup script
```

## Notes

- The Flask backend uses threading for background scraping jobs
- All processed files are saved in `data/processed/`
- The frontend connects to `http://localhost:8000` by default
- CORS is enabled for all origins (development mode)
