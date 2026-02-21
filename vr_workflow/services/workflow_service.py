from datetime import datetime
from vr_workflow.models import Stage, ChecklistItem, Task


def toggle_checklist_item(session, item_id):

    item = session.query(ChecklistItem).filter_by(id=item_id).first()

    if not item:
        return None

    # Toggle
    item.completed = not item.completed
    session.commit()

    stage = session.query(Stage).filter_by(id=item.stage_id).first()
    items = session.query(ChecklistItem).filter_by(stage_id=stage.id).all()

    # Əgər hamısı tamamdırsa
    if all(i.completed for i in items):

        stage.status = "completed"
        stage.completed_at = datetime.now()
        session.commit()

        # Növbəti mərhələni tap
        next_stage = session.query(Stage).filter(
            Stage.task_id == stage.task_id,
            Stage.status == "pending"
        ).first()

        if next_stage:
            next_stage.status = "active"
            session.commit()

            return {
                "stage_completed": stage,
                "next_stage": next_stage,
                "task_completed": False
            }

        else:
            task = session.query(Task).filter_by(id=stage.task_id).first()
            task.status = "completed"
            session.commit()

            return {
                "stage_completed": stage,
                "next_stage": None,
                "task_completed": True,
                "task": task
            }

    return {
        "stage_completed": None
    }