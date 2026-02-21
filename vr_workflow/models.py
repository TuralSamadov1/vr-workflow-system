from sqlalchemy import Column, Integer, String, Boolean, DateTime
from vr_workflow.database import Base

# ---------------- MODELLƏR ---------------- #

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    status = Column(String, default="active")
    team_id = Column(Integer)  # YENİ


class Stage(Base):
    __tablename__ = "stages"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    name = Column(String)
    assigned_user = Column(String)
    status = Column(String, default="pending")  # pending / active / completed

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    deadline = Column(DateTime)


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True)
    stage_id = Column(Integer)
    text = Column(String)
    completed = Column(Boolean, default=False)

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
    user_id = Column(Integer)  # User model id
    role = Column(String)  # team_lead / worker