from datetime import datetime, timedelta
from vr_workflow.models import Task, Stage, ChecklistItem


def create_reels_task(session, creator_id, montage_user_id):

    # TASK
    task = Task(title="Reels Çəkilişi")
    session.add(task)
    session.commit()

    # STAGE 1 – Çəkiliş
    stage1 = Stage(
        task_id=task.id,
        name="Çəkiliş",
        assigned_user=str(creator_id),
        status="active",
        started_at=datetime.now(),
        deadline=datetime.now() + timedelta(minutes=3)
    )
    session.add(stage1)
    session.commit()

    # STAGE 2 – Montaj
    stage2 = Stage(
        task_id=task.id,
        name="Montaj",
        assigned_user=str(montage_user_id),
        status="pending",
        deadline=datetime.now() + timedelta(minutes=5)
    )
    session.add(stage2)
    session.commit()

    # Checklist
    items = [
        "Ssenari hazırdır",
        "Məkan hazırdır",
        "Çəkiliş edildi"
    ]

    for text in items:
        session.add(ChecklistItem(stage_id=stage1.id, text=text))

    session.commit()

    return stage1.id