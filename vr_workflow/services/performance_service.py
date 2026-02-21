from vr_workflow.models import Stage, User


def calculate_user_score(session, telegram_id):

    stages = session.query(Stage).filter(
        Stage.assigned_user == telegram_id,
        Stage.status == "completed"
    ).all()

    total = len(stages)
    late_count = 0
    total_time = 0

    for stage in stages:

        if stage.started_at and stage.completed_at:
            duration = (stage.completed_at - stage.started_at).total_seconds()
            total_time += duration

        if stage.deadline and stage.completed_at:
            if stage.completed_at > stage.deadline:
                late_count += 1

    avg_time = total_time / total if total > 0 else 0
    avg_minutes = round(avg_time / 60, 2)

    score = total * 10 - late_count * 3

    return {
        "total": total,
        "late_count": late_count,
        "avg_minutes": avg_minutes,
        "score": score
    }


def generate_leaderboard(session):

    users = session.query(User).all()
    leaderboard = []

    for user in users:

        data = calculate_user_score(session, user.telegram_id)

        leaderboard.append((user.name, data["score"]))

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    return leaderboard