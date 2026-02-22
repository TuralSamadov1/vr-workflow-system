from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from vr_workflow.database import SessionLocal
from vr_workflow.models import Task

app = FastAPI()

templates = Jinja2Templates(directory="vr_workflow/templates")


@app.get("/")
def root():
    return {"status": "VR Workflow API işləyir"}


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    session = SessionLocal()
    tasks = session.query(Task).all()

    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "tasks": tasks}
    )