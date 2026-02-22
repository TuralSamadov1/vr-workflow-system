# vr_workflow/services/audit_service.py

from vr_workflow.models import AuditLog


class AuditService:

    @staticmethod
    def log(session, user_id: int | None, entity_type: str, entity_id: int, action: str):
        log = AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action
        )

        session.add(log)