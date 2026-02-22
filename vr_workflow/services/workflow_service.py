from datetime import datetime
from sqlalchemy import or_, and_
from vr_workflow.models import Stage, ChecklistItem, Task
from vr_workflow.services.audit_service import AuditService


def _find_next_stage(session, stage):

    # Yeni modeldə order ilə, köhnə datada isə id ilə irəlilə
    return session.query(Stage).filter(
        Stage.task_id == stage.task_id,
        Stage.status == "pending",
        or_(
            Stage.order > (stage.order or 0),
            and_(Stage.order == (stage.order or 0), Stage.id > stage.id)
        )
    ).order_by(Stage.order.asc(), Stage.id.asc()).first()


def toggle_checklist_item(session, item_id, user_id):

    item = session.query(ChecklistItem).filter_by(id=item_id).first()
    if not item:
        return None

    item.completed = not item.completed

    AuditService.log(
        session=session,
        user_id=user_id,
        entity_type="checklist_item",
        entity_id=item.id,
        action="toggled"
    )

    stage = session.query(Stage).filter_by(id=item.stage_id).first()
    items = session.query(ChecklistItem).filter_by(stage_id=stage.id).all()

    # Əgər hamısı tamamdırsa
    if all(i.completed for i in items):

        stage.status = "completed"
        AuditService.log(
            session=session,
            user_id=user_id,
            entity_type="stage",
            entity_id=stage.id,
            action="completed"
        )
        stage.completed_at = datetime.now()

        next_stage = _find_next_stage(session, stage)

        if next_stage:
            next_stage.status = "active"
            next_stage.started_at = datetime.now()
            return next_stage.id   # <-- SADƏ INT

        else:
            task = session.query(Task).filter_by(id=stage.task_id).first()
            task.status = "waiting_approval"
            AuditService.log(
                session=session,
                user_id=user_id,
                entity_type="task",
                entity_id=task.id,
                action="waiting_approval"
            )
            return stage.id       # <-- sonuncu stage qalır

    return stage.id               # <-- həmişə INT qaytarır


def request_stage_revision(session, stage_id):

    stage = session.query(Stage).filter_by(id=stage_id).first()

    if not stage:
        return None

    # Eyni task daxilində tək bir aktiv stage saxlayaq
    session.query(Stage).filter(
        Stage.task_id == stage.task_id,
        Stage.id != stage.id,
        Stage.status == "active"
    ).update({"status": "pending", "started_at": None}, synchronize_session=False)

    stage.status = "active"
    stage.started_at = datetime.now()
    stage.completed_at = None
    stage.revision_count = (stage.revision_count or 0) + 1

    checklist_items = session.query(ChecklistItem).filter_by(stage_id=stage.id).all()
    for item in checklist_items:
        item.completed = False

    # Bu stage-dən sonrakı mərhələləri geri pending et
    later_stages = session.query(Stage).filter(
        Stage.task_id == stage.task_id,
        Stage.order > stage.order,
        Stage.status.in_(["active", "completed"])
    ).all()

    for later_stage in later_stages:
        later_stage.status = "pending"
        later_stage.started_at = None
        later_stage.completed_at = None

    task = session.query(Task).filter_by(id=stage.task_id).first()
    if task and task.status == "completed":
        task.status = "active"



    return {
        "stage": stage,
        "revision_count": stage.revision_count
    }

