from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import time

from src.core.scraping.scrape_and_classify import run_scraper

router = APIRouter()

# Simple in-memory job status
JOB_STATUS: Dict[str, Dict[str, Any]] = {}

def _models_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..", "models", "distilbert_finetuned"))

def _processed_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..", "data", "processed"))

os.makedirs(_processed_dir(), exist_ok=True)

class ScrapeRequest(BaseModel):
    city: str
    categories: Optional[List[str]] = None
    output_filename: Optional[str] = None

def _background_run(job_id: str, city: str, categories: Optional[List[str]]):
    try:
        JOB_STATUS[job_id] = {"status": "running", "started_at": time.time()}
        filename = f"{city.replace(' ', '_')}.xlsx"
        if categories:
            safe_cats = "_".join([c.split()[0] for c in categories])[:30]
            filename = f"{city.replace(' ', '_')}_{safe_cats}.xlsx"
        if JOB_STATUS[job_id].get("output_filename_override"):
            filename = JOB_STATUS[job_id]["output_filename_override"]
        output_path = os.path.join(_processed_dir(), filename)
        model_path = _models_dir()
        run_scraper(city, model_path, output_path, categories or None)
        JOB_STATUS[job_id].update({
            "status": "completed",
            "finished_at": time.time(),
            "output_file": output_path,
        })
    except Exception as exc:  # noqa: BLE001
        JOB_STATUS[job_id].update({
            "status": "failed",
            "finished_at": time.time(),
            "error": str(exc),
        })

@router.post("/scrape")
async def scrape_data(request: ScrapeRequest, background_tasks: BackgroundTasks):
    job_id = f"{int(time.time()*1000)}"
    JOB_STATUS[job_id] = {
        "status": "queued",
        "city": request.city,
        "categories": request.categories or [],
        "requested_at": time.time(),
        "output_filename_override": request.output_filename,
    }
    background_tasks.add_task(_background_run, job_id, request.city, request.categories)
    return {"job_id": job_id, "message": "Scraping started"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    return JOB_STATUS.get(job_id, {"status": "unknown", "error": "job not found"})

@router.get("/data")
async def list_data():
    directory = _processed_dir()
    files = []
    for name in os.listdir(directory):
        if name.lower().endswith((".csv", ".xlsx")):
            path = os.path.join(directory, name)
            stat = os.stat(path)
            files.append({
                "filename": name,
                "path": path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {"files": files}

@router.get("/export/{filename}")
async def export_file(filename: str):
    path = os.path.join(_processed_dir(), filename)
    if not os.path.exists(path):
        return {"error": "File not found"}
    media = (
        "text/csv" if filename.lower().endswith(".csv")
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return FileResponse(path, media_type=media, filename=filename)
