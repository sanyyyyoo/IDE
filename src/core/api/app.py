from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import os
import time
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
from io import StringIO

from src.core.scraping.scrape_and_classify import run_scraper

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Simple in-memory job status
JOB_STATUS: Dict[str, Dict[str, Any]] = {}

# Custom logging handler to capture logs for jobs
class JobLogHandler(logging.Handler):
    def __init__(self, job_id: str):
        super().__init__()
        self.job_id = job_id
        self.setLevel(logging.INFO)
        
    def emit(self, record):
        # Only capture logs from scraping module or root logger
        if 'scraping' in record.name.lower() or record.name == 'root' or 'scrape' in record.name.lower():
            log_message = self.format(record)
            if self.job_id in JOB_STATUS:
                if 'logs' not in JOB_STATUS[self.job_id]:
                    JOB_STATUS[self.job_id]['logs'] = []
                JOB_STATUS[self.job_id]['logs'].append({
                    'message': log_message,
                    'level': record.levelname,
                    'time': time.time()
                })
                # Keep only last 200 logs
                if len(JOB_STATUS[self.job_id]['logs']) > 200:
                    JOB_STATUS[self.job_id]['logs'] = JOB_STATUS[self.job_id]['logs'][-200:]

def _get_project_root() -> str:
    """Find the project root directory by looking for src/ directory."""
    current_file = os.path.abspath(__file__)  # src/core/api/app.py
    current_dir = os.path.dirname(current_file)
    
    # Walk up the directory tree to find project root
    # Project root should contain 'src' and 'models' directories
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        # Check if this directory contains 'src' and 'models'
        if os.path.exists(os.path.join(current_dir, 'src')) and os.path.exists(os.path.join(current_dir, 'models')):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    
    # Fallback: go up 4 levels from app.py
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))

def _models_dir() -> str:
    """Get the models directory path."""
    env_model_path = os.getenv("MODEL_PATH")
    if env_model_path:
        env_model_path = os.path.abspath(env_model_path)
        if os.path.isdir(env_model_path):
            return env_model_path
        raise FileNotFoundError(
            f"Environment variable MODEL_PATH is set but the directory was not found: {env_model_path}\n"
            "Please ensure the model folder exists or unset MODEL_PATH."
        )

    project_root = _get_project_root()
    model_path = os.path.join(project_root, "models", "distilbert_finetuned")
    
    # Verify the path exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model directory not found: {model_path}\n"
            f"Project root: {project_root}\n"
            f"Please ensure the model is located at: {model_path}"
        )
    
    return model_path

def _processed_dir() -> str:
    """Get the processed data directory path."""
    project_root = _get_project_root()
    return os.path.join(project_root, "output")

os.makedirs(_processed_dir(), exist_ok=True)

def _background_run(job_id: str, city: str, categories: Optional[List[str]]):
    """Run scraper in background thread."""
    # Set up logging handler for this job
    job_handler = JobLogHandler(job_id)
    job_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"))
    
    # Get root logger and add handler
    root_logger = logging.getLogger()
    root_logger.addHandler(job_handler)
    
    try:
        JOB_STATUS[job_id] = {"status": "running", "started_at": time.time(), "logs": []}
        filename = f"{city.replace(' ', '_')}.xlsx"
        if categories:
            safe_cats = "_".join([c.split()[0] for c in categories])[:30]
            filename = f"{city.replace(' ', '_')}_{safe_cats}.xlsx"
        if JOB_STATUS[job_id].get("output_filename_override"):
            filename = JOB_STATUS[job_id]["output_filename_override"]
        output_path = os.path.join(_processed_dir(), filename)
        
        # Get and verify model path
        try:
            model_path = _models_dir()
        except FileNotFoundError as e:
            JOB_STATUS[job_id].update({
                "status": "failed",
                "finished_at": time.time(),
                "error": str(e),
            })
            root_logger.removeHandler(job_handler)
            return
        
        run_scraper(city, model_path, output_path, selected_categories=categories, limit=None)
        JOB_STATUS[job_id].update({
            "status": "completed",
            "finished_at": time.time(),
            "output_file": output_path,
        })
    except Exception as exc:
        JOB_STATUS[job_id].update({
            "status": "failed",
            "finished_at": time.time(),
            "error": str(exc),
        })
    finally:
        # Remove handler when done
        root_logger.removeHandler(job_handler)

@app.route('/scrape', methods=['POST'])
def scrape_data():
    """Start a scraping job."""
    data = request.get_json()
    city = data.get('city', '')
    categories = data.get('categories')
    output_filename = data.get('output_filename')
    
    if not city:
        return jsonify({"error": "City is required"}), 400
    
    job_id = f"{int(time.time()*1000)}"
    JOB_STATUS[job_id] = {
        "status": "queued",
        "city": city,
        "categories": categories or [],
        "requested_at": time.time(),
        "output_filename_override": output_filename,
    }
    
    # Start background thread
    thread = threading.Thread(target=_background_run, args=(job_id, city, categories))
    thread.daemon = True
    thread.start()
    
    return jsonify({"job_id": job_id, "message": "Scraping started"})

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id: str):
    """Get status of a scraping job."""
    status = JOB_STATUS.get(job_id, {"status": "unknown", "error": "job not found"})
    # Include logs in response
    response = {
        "status": status.get("status", "unknown"),
        "error": status.get("error"),
        "output_file": status.get("output_file"),
        "logs": status.get("logs", []),
        "message": status.get("message")
    }
    return jsonify(response)

@app.route('/data', methods=['GET'])
def list_data():
    """Get data from the most recent file."""
    try:
        directory = _processed_dir()
        files = []
        if os.path.exists(directory):
            for name in os.listdir(directory):
                if name.lower().endswith((".csv", ".xlsx")):
                    path = os.path.join(directory, name)
                    try:
                        stat = os.stat(path)
                        files.append({
                            "filename": name,
                            "path": path,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                        })
                    except OSError:
                        # Skip files that can't be accessed
                        continue
        
        if not files:
            return jsonify([])
        
        # Get the most recent file
        files.sort(key=lambda x: x["modified"], reverse=True)
        most_recent_file = files[0]["path"]
        
        try:
            # Read the file based on extension
            print(f"[INFO] Reading file: {most_recent_file}")
            if most_recent_file.lower().endswith(".xlsx"):
                try:
                    df = pd.read_excel(most_recent_file, engine='openpyxl')
                except ImportError:
                    return jsonify({"error": "openpyxl library is required to read Excel files. Install it with: pip install openpyxl"}), 500
            else:
                df = pd.read_csv(most_recent_file)
            
            print(f"[INFO] File read successfully. Rows: {len(df)}, Columns: {list(df.columns)}")
            
            # Convert to list of dictionaries, replacing NaN with empty strings
            data = df.fillna('').to_dict('records')
            print(f"[INFO] Returning {len(data)} records")
            return jsonify(data)
        except Exception as e:
            import traceback
            error_msg = f"Error reading file {most_recent_file}: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] {error_msg}")
            return jsonify({"error": f"Error reading file: {str(e)}"}), 500
    except Exception as e:
        import traceback
        error_msg = f"Error in /data endpoint: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_msg}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Server is running"})

@app.route('/export/<filename>', methods=['GET'])
def export_file(filename: str):
    """Download a processed file."""
    path = os.path.join(_processed_dir(), filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    
    # Determine MIME type
    if filename.lower().endswith(".csv"):
        mimetype = "text/csv"
    else:
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return send_file(path, mimetype=mimetype, as_attachment=True, download_name=filename)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "API is running"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
