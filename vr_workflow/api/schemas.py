from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RegisterSchema(BaseModel):
    name: str
    telegram_id: str
    password: str

class LoginSchema(BaseModel):
    telegram_id: str
    password: str

class TaskSchema(BaseModel):
    id: int
    title: str
    status: str
    team_id: Optional[int]

    class Config:
        orm_mode = True

class StageSchema(BaseModel):
    id: int
    task_id: int
    name: str
    order: int
    assigned_role: Optional[str]
    status: str
    revision_count: int
    deadline: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True

class AnalyticsSchema(BaseModel):
    total_tasks: int
    active_tasks: int
    completed_tasks: int
    total_stages: int
    completed_stages: int
    overdue_stages: int
