from sqlalchemy.orm import Session
from vr_workflow.models import Stage


class StageRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs):
        stage = Stage(**kwargs)
        self.db.add(stage)
        return stage