from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from vr_workflow.database import SessionLocal, init_db
from vr_workflow.models import Task

app = FastAPI()


@app.on_event("startup")
def startup_event():
    init_db()


def _get_templates():
    try:
        return Jinja2Templates(directory="vr_workflow/templates")
    except AssertionError:
        return None


@app.get("/")
def root():
    return {"status": "VR Workflow API işləyir"}


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    templates = _get_templates()

    if templates is None:
        return HTMLResponse(
            "Jinja2 paketi quraşdırılmayıb. Bu komandanı işə salın: pip install jinja2",
            status_code=500
        )

    session = SessionLocal()
    try:
        tasks = session.query(Task).all()

        return templates.TemplateResponse(
            "admin.html",
            {"request": request, "tasks": tasks}
        )
    finally:
        session.close()
