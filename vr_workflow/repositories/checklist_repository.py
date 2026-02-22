from sqlalchemy.orm import Session
from vr_workflow.models import ChecklistItem


class ChecklistRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs):
        item = ChecklistItem(**kwargs)
        self.db.add(item)
        return item