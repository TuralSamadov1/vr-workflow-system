from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from vr_workflow.database import Base
from sqlalchemy.orm import relationship

# ---------------- MODELLƏR ---------------- #

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    status = Column(String, default="active")
    team_id = Column(Integer, ForeignKey("teams.id"))

    stages = relationship("Stage", back_populates="task")


class Stage(Base):
    __tablename__ = "stages"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    name = Column(String)
    assigned_user = Column(String)
    assigned_role = Column(String)
    status = Column(String, default="pending")
    order = Column(Integer, default=0)
    revision_count = Column(Integer, default=0)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    deadline = Column(DateTime)

    task = relationship("Task", back_populates="stages")
    checklist_items = relationship("ChecklistItem", back_populates="stage")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True)
    stage_id = Column(Integer, ForeignKey("stages.id"))
    text = Column(String)
    completed = Column(Boolean, default=False)

    stage = relationship("Stage", back_populates="checklist_items")

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    completed_stages = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    name = Column(String)
    role = Column(String, default="worker")  # admin / worker
    password = Column(String)

# ---------------- TEMPLATE MODELLƏR ---------------- #

class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class WorkflowTemplateStage(Base):
    __tablename__ = "workflow_template_stages"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer)
    name = Column(String)
    order = Column(Integer)
    assigned_role = Column(String)


class WorkflowTemplateChecklist(Base):
    __tablename__ = "workflow_template_checklists"

    id = Column(Integer, primary_key=True)
    template_stage_id = Column(Integer)
    text = Column(String)

# ---------------- TEAM MODELLƏR ---------------- #

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # team_lead / worker
