# Quick Start Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Start the Flask Backend

```bash
python run_server.py
```

The server will start on `http://localhost:8000`

## 3. Open the Frontend

Simply open `frontend/index.html` in your web browser, or use a simple HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

## Features

✅ **City Input** - Enter any city name  
✅ **Field Selection** - Choose which fields to scrape (name, address, phone, category)  
✅ **Category Selection** - Select from 26 business categories  
✅ **Real-time Logs** - See scraping progress and activity in real-time  
✅ **Status Display** - Visual status indicators and progress bars  

## Usage

1. Enter a city name (e.g., "Mumbai", "Delhi")
2. Select fields you want to scrape
3. Choose one or more business categories
4. Click "Start Scraping"
5. Watch the logs for real-time updates
6. Download results when complete

## API Endpoints

- `POST /scrape` - Start scraping
- `GET /status/<job_id>` - Check job status
- `GET /data` - List processed files
- `GET /export/<filename>` - Download file
- `GET /health` - Health check
