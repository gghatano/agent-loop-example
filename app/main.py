import json
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from app import formatting

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI()
templates = Jinja2Templates(directory=ROOT / "app" / "templates")
templates.env.filters.update(
    yen=formatting.yen,
    status_label=formatting.status_label,
    period=lambda p: formatting.period(p["start"], p["end"]),
    days=lambda p: formatting.days(p["start"], p["end"]),
)
templates.env.globals.update(member_role=formatting.member_role, statuses=formatting.STATUSES)


def get_projects() -> list[dict]:
    """案件データの取得口。テストでは app.dependency_overrides で差し替える。"""
    return json.loads((ROOT / "fixtures" / "projects.json").read_text(encoding="utf-8"))


Projects = Annotated[list[dict], Depends(get_projects)]


@app.get("/static/style.css")
def style():
    # デザインの正である mock/style.css をそのまま配信する（複製しない）
    return FileResponse(ROOT / "mock" / "style.css", media_type="text/css")


@app.get("/projects")
def project_list(request: Request, projects: Projects):
    return templates.TemplateResponse(request, "list.html", {"projects": projects})


@app.get("/projects/new")
def project_new(request: Request):
    return templates.TemplateResponse(request, "new.html", {})


@app.get("/projects/{project_id}")
def project_detail(request: Request, project_id: int, projects: Projects):
    project = next((p for p in projects if p["id"] == project_id), None)
    if project is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request, "detail.html", {"project": project})
