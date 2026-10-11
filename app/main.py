import json
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI()
templates = Jinja2Templates(directory=ROOT / "app" / "templates")

STATUS_LABELS = {"active": "進行中", "paused": "保留", "closed": "完了"}


def _ymd(value: str) -> str:
    return value.replace("-", "/")


def _period(project: dict) -> str:
    return f"{_ymd(project['start'])} – {_ymd(project['end'])}"


def _days(project: dict) -> int:
    return (date.fromisoformat(project["end"]) - date.fromisoformat(project["start"])).days + 1


templates.env.filters["yen"] = lambda n: f"¥{n:,}"
templates.env.filters["status_label"] = STATUS_LABELS.__getitem__
templates.env.filters["period"] = _period
templates.env.filters["days"] = _days


@app.get("/static/style.css")
def style():
    # デザインの正である mock/style.css をそのまま配信する（複製しない）
    return FileResponse(ROOT / "mock" / "style.css", media_type="text/css")


def load_projects() -> list[dict]:
    return json.loads((ROOT / "fixtures" / "projects.json").read_text(encoding="utf-8"))


@app.get("/projects")
def project_list(request: Request):
    return templates.TemplateResponse(request, "list.html", {"projects": load_projects()})


@app.get("/projects/new")
def project_new(request: Request):
    return templates.TemplateResponse(request, "new.html", {})


@app.get("/projects/{project_id}")
def project_detail(request: Request, project_id: int):
    project = next((p for p in load_projects() if p["id"] == project_id), None)
    if project is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request, "detail.html", {"project": project})
