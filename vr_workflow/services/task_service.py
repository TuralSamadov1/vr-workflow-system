from datetime import datetime, timedelta
from vr_workflow.models import Task, Stage, ChecklistItem
from vr_workflow.repositories.task_repository import TaskRepository
from vr_workflow.repositories.stage_repository import StageRepository
from vr_workflow.repositories.checklist_repository import ChecklistRepository


from datetime import datetime, timedelta


def create_reels_task(session, creator_id, montage_user_id):

    task_repo = TaskRepository(session)
    stage_repo = StageRepository(session)
    checklist_repo = ChecklistRepository(session)

    # TASK
    task = task_repo.create(
        title="Reels Çəkilişi",
        team_id=1,  # hələlik sabit qoyuruq
        created_by=creator_id
    )

    session.flush()

    # STAGE 1 – Çəkiliş
    stage1 = stage_repo.create(
        task_id=task.id,
        name="Çəkiliş",
        assigned_user=str(creator_id),
        status="active",
        started_at=datetime.now(),
        deadline=datetime.now() + timedelta(minutes=3)
    )

    session.flush()

    # STAGE 2 – Montaj
    stage_repo.create(
        task_id=task.id,
        name="Montaj",
        assigned_user=str(montage_user_id),
        status="pending",
        deadline=datetime.now() + timedelta(minutes=5)
    )

    # Checklist
    items = [
        "Ssenari hazırdır",
        "Məkan hazırdır",
        "Çəkiliş edildi"
    ]

    for text in items:
        checklist_repo.create(
            stage_id=stage1.id,
            text=text
        )

    session.commit()
    session.refresh(task)

    return stage1.id
