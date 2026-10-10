import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI()
templates = Jinja2Templates(directory=ROOT / "app" / "templates")


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
