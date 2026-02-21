from fastapi import FastAPI, HTTPException, Depends
from vr_workflow.database import SessionLocal
from vr_workflow.models import Task, TeamMember, User, Stage, Team
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from vr_workflow.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from typing import List
from vr_workflow.api.schemas import (
    RegisterSchema,
    LoginSchema,
    AnalyticsSchema,
    TaskSchema,
    StageSchema
)
from pydantic import BaseModel



app = FastAPI()

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        telegram_id: str = payload.get("sub")
        role: str = payload.get("role")

        if telegram_id is None:
            raise Exception()

        return {
            "telegram_id": telegram_id,
            "role": role
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
def root():
    return {"message": "Workflow API işləyir 🚀"}

@app.get("/tasks", response_model=List[TaskSchema])
def list_tasks(current_user: dict = Depends(get_current_user)):

    session = SessionLocal()

    if current_user["role"] == "admin":
        tasks = session.query(Task).all()

    else:
        user = session.query(User).filter_by(
            telegram_id=current_user["telegram_id"]
        ).first()

        memberships = session.query(TeamMember).filter_by(
            user_id=user.id
        ).all()

        team_ids = [m.team_id for m in memberships]

        tasks = session.query(Task).filter(
            Task.team_id.in_(team_ids)
        ).all()

    result = []

    for task in tasks:
        result.append({
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "team_id": task.team_id
        })

    session.close()
    return result

@app.post("/register")
def register(data: RegisterSchema):

    session = SessionLocal()

    existing = session.query(User).filter_by(
        telegram_id=data.telegram_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        name=data.name,
        telegram_id=data.telegram_id,
        password=hash_password(data.password),
        role="worker"
    )

    session.add(user)
    session.commit()
    session.close()

    return {"message": "User created"}

@app.post("/login")
def login(data: LoginSchema):

    session = SessionLocal()

    user = session.query(User).filter_by(
        telegram_id=data.telegram_id
    ).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.telegram_id,
        "role": user.role
    })

    session.close()

    return {"access_token": token}

@app.get("/admin-only")
def admin_area(current_user: dict = Depends(get_current_user)):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    return {"message": "Admin panel access granted"}

@app.get("/my-stages", response_model=List[StageSchema])
def my_stages(current_user: dict = Depends(get_current_user)):

    session = SessionLocal()

    stages = session.query(Stage).filter(
        Stage.assigned_user == current_user["telegram_id"]
    ).all()

    result = []

    for stage in stages:
        result.append({
            "id": stage.id,
            "task_id": stage.task_id,
            "name": stage.name,
            "status": stage.status,
            "deadline": stage.deadline,
            "started_at": stage.started_at,
            "completed_at": stage.completed_at
        })

    session.close()

    return result

@app.get("/analytics", response_model=AnalyticsSchema)
def analytics(current_user: dict = Depends(get_current_user)):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    session = SessionLocal()

    total_tasks = session.query(Task).count()
    active_tasks = session.query(Task).filter(
        Task.status == "active"
    ).count()

    completed_tasks = session.query(Task).filter(
        Task.status == "completed"
    ).count()

    total_stages = session.query(Stage).count()

    overdue_stages = session.query(Stage).filter(
        Stage.status == "overdue"
    ).count()

    completed_stages = session.query(Stage).filter(
        Stage.status == "completed"
    ).count()

    session.close()

    return {
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks,
        "total_stages": total_stages,
        "completed_stages": completed_stages,
        "overdue_stages": overdue_stages
    }

class TeamCreateSchema(BaseModel):
    name: str


@app.post("/teams")
def create_team(
    data: TeamCreateSchema,
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    session = SessionLocal()

    existing = session.query(Team).filter_by(name=data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Team already exists")

    team = Team(name=data.name)
    session.add(team)
    session.commit()
    session.close()

    return {"message": "Team created"}

class AddUserToTeamSchema(BaseModel):
    telegram_id: str
    team_name: str
    role: str  # team_lead / worker


@app.post("/teams/add-user")
def add_user_to_team(
    data: AddUserToTeamSchema,
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    session = SessionLocal()

    user = session.query(User).filter_by(
        telegram_id=data.telegram_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    team = session.query(Team).filter_by(name=data.team_name).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    membership = TeamMember(
        team_id=team.id,
        user_id=user.id,
        role=data.role
    )

    session.add(membership)
    session.commit()
    session.close()

    return {"message": "User added to team"}