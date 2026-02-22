from sqlalchemy.orm import Session
from vr_workflow.models import Task


class TaskRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str, team_id: int, created_by: int):
        task = Task(
            title=title,
            team_id=team_id,
            created_by=created_by
        )
        self.db.add(task)
        self.db.add(task)
        return task
    
    def get_by_id(self, task_id: int):
        return self.db.query(Task).filter(Task.id == task_id).first()

    def list_by_team(self, team_id: int):
        return self.db.query(Task).filter(Task.team_id == team_id).all()