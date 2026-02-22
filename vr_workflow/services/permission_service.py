# vr_workflow/services/permission_service.py

class PermissionDenied(Exception):
    pass


class PermissionService:

    @staticmethod
    def can_toggle_checklist(user_role: str, stage_assigned_user: str, current_user_telegram_id: str):
        if user_role == "admin":
            return True

        if stage_assigned_user == current_user_telegram_id:
            return True

        raise PermissionDenied("You do not have permission to toggle this checklist item")