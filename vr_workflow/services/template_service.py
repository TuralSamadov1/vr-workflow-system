from vr_workflow.models import (
    WorkflowTemplate,
    WorkflowTemplateStage,
    WorkflowTemplateChecklist,
    Task,
    Stage,
    ChecklistItem
)
from datetime import datetime, timedelta


# ---------------- TEMPLATE YARAT ---------------- #

def create_reels_template(session):

    # Əgər artıq varsa, yenidən yaratma
    existing = session.query(WorkflowTemplate).filter_by(
        name="Reels Production"
    ).first()

    if existing:
        return existing

    template = WorkflowTemplate(name="Reels Production")
    session.add(template)
    session.commit()

    # STAGE 1
    stage1 = WorkflowTemplateStage(
        template_id=template.id,
        name="Çəkiliş",
        order=1
    )
    session.add(stage1)
    session.commit()

    checklist1 = [
        "Ssenari hazırdır",
        "Məkan hazırdır",
        "Çəkiliş edildi"
    ]

    for text in checklist1:
        session.add(
            WorkflowTemplateChecklist(
                template_stage_id=stage1.id,
                text=text
            )
        )

    # STAGE 2
    stage2 = WorkflowTemplateStage(
        template_id=template.id,
        name="Montaj",
        order=2
    )
    session.add(stage2)
    session.commit()

    checklist2 = [
        "Montaj başladı",
        "Montaj bitdi"
    ]

    for text in checklist2:
        session.add(
            WorkflowTemplateChecklist(
                template_stage_id=stage2.id,
                text=text
            )
        )

    session.commit()

    return template


# ---------------- TEMPLATE-DƏN TASK YARAT ---------------- #

def create_task_from_template(session, template_name, creator_id, montage_user_id):

    template = session.query(WorkflowTemplate).filter_by(
        name=template_name
    ).first()

    if not template:
        return None

    task = Task(title=template.name)
    session.add(task)
    session.commit()

    template_stages = session.query(WorkflowTemplateStage).filter_by(
        template_id=template.id
    ).order_by(WorkflowTemplateStage.order).all()

    first_stage_id = None

    for index, t_stage in enumerate(template_stages):

        assigned_user = (
            str(creator_id) if index == 0 else str(montage_user_id)
        )

        status = "active" if index == 0 else "pending"

        stage = Stage(
            task_id=task.id,
            name=t_stage.name,
            assigned_user=assigned_user,
            status=status,
            started_at=datetime.now() if index == 0 else None,
            deadline=datetime.now() + timedelta(minutes=5)
        )

        session.add(stage)
        session.commit()

        if index == 0:
            first_stage_id = stage.id

        template_checklists = session.query(
            WorkflowTemplateChecklist
        ).filter_by(template_stage_id=t_stage.id).all()

        for item in template_checklists:
            session.add(
                ChecklistItem(
                    stage_id=stage.id,
                    text=item.text
                )
            )

        session.commit()

    return first_stage_id