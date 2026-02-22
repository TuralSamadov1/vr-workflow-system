from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from vr_workflow.models import Task

app = FastAPI()

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
