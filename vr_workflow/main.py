import asyncio
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from vr_workflow.database import Base, engine, SessionLocal
from vr_workflow.models import Task, Stage, ChecklistItem, UserStats, User
from vr_workflow.services.task_service import create_reels_task
from vr_workflow.services.workflow_service import toggle_checklist_item
from vr_workflow.services.performance_service import calculate_user_score, generate_leaderboard
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from vr_workflow.services.template_service import (
    create_reels_template,
    create_task_from_template
)

BOT_TOKEN = "8446148700:AAFpzUpbKoAAeKN9ureWY8YHkY9yctUbdkw"
ADMIN_ID = 889375033  # öz ID-ni yaz
MONTAGE_USER_ID = 889375033  # test üçün eyni qoya bilərsən

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


session = SessionLocal()

Base.metadata.create_all(engine)

# ---------------- COMMANDS ---------------- #


@dp.message(Command("create_task"))
async def create_task(message: types.Message):

    stage_id = create_task_from_template(
        session,
        "Reels Production",
        message.from_user.id,
        MONTAGE_USER_ID
    )

    await send_stage_view(message.chat.id, stage_id)


# ---------------- UI ---------------- #

async def send_stage_view(chat_id, stage_id):
    stage = session.query(Stage).filter_by(id=stage_id).first()
    items = session.query(ChecklistItem).filter_by(stage_id=stage_id).all()

    text = f"📌 {stage.name} mərhələsi\n\n"

    keyboard = []

    for item in items:
        status = "☑️" if item.completed else "⬜"
        text += f"{status} {item.text}\n"

        keyboard.append([
            InlineKeyboardButton(
                text=f"{status} {item.text}",
                callback_data=f"toggle_{item.id}"
            )
        ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await bot.send_message(chat_id, text, reply_markup=markup)


# ---------------- TOGGLE ---------------- #

@dp.callback_query()
async def handle_toggle(callback: types.CallbackQuery):

    item_id = int(callback.data.split("_")[1])

    result = toggle_checklist_item(session, item_id)

    if result and result.get("stage_completed"):

        stage = result["stage_completed"]

        await bot.send_message(
            int(stage.assigned_user),
            f"✅ Sənin '{stage.name}' mərhələn tamamlandı"
        )

        if result.get("next_stage"):

            next_stage = result["next_stage"]

            await bot.send_message(
                int(next_stage.assigned_user),
                f"🎬 Yeni mərhələ başladı: {next_stage.name}"
            )

        elif result.get("task_completed"):

            task = result["task"]

            await bot.send_message(
                ADMIN_ID,
                f"🏁 Layihə tamamlandı: {task.title}"
            )

    await callback.message.delete()

    stage = session.query(Stage).filter_by(
        id=session.query(ChecklistItem).filter_by(id=item_id).first().stage_id
    ).first()

    await send_stage_view(callback.message.chat.id, stage.id)

@dp.message(Command("my_tasks"))
async def my_tasks(message: types.Message):

    stages = session.query(Stage).filter(
        Stage.assigned_user == str(message.from_user.id),
        Stage.status == "active"
    ).all()

    if not stages:
        await message.answer("Aktiv mərhələ yoxdur.")
        return

    for stage in stages:
        await send_stage_view(message.chat.id, stage.id)

@dp.message(Command("profile"))
async def profile(message: types.Message):

    data = calculate_user_score(session, str(message.from_user.id))

    if data["total"] == 0:
        await message.answer("Hələ tamamlanan mərhələ yoxdur.")
        return

    text = f"""
👤 PROFİL

✅ Tamamlanan mərhələlər: {data["total"]}
⚠️ Gecikən mərhələlər: {data["late_count"]}
⏱ Orta icra müddəti: {data["avg_minutes"]} dəqiqə
🏆 Performance balı: {data["score"]}
"""

    await message.answer(text)

@dp.message(Command("menu"))
async def menu(message: types.Message):

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Aktiv Tasklar", callback_data="menu_active")],
        [InlineKeyboardButton(text="✅ Tamamlananlar", callback_data="menu_completed")],
        [InlineKeyboardButton(text="👤 Profil", callback_data="menu_profile")],
        [InlineKeyboardButton(text="ℹ️ Əmrlər", callback_data="menu_help")]
    ])

    await message.answer("📊 İdarə Paneli", reply_markup=keyboard)

@dp.callback_query()
async def menu_handler(callback: types.CallbackQuery):

    if callback.data == "menu_active":
        await my_tasks(callback.message)

    elif callback.data == "menu_completed":
        stages = session.query(Stage).filter(
            Stage.assigned_user == str(callback.from_user.id),
            Stage.status == "completed"
        ).all()

        if not stages:
            await callback.message.answer("Tamamlanan mərhələ yoxdur.")
            return

        for stage in stages:
            await callback.message.answer(f"✅ {stage.name}")

    elif callback.data == "menu_profile":
        await profile(callback.message)

    elif callback.data == "menu_help":
        await callback.message.answer("""
Əmrlər:
/create_task
/my_tasks
/profile
/menu
""")

@dp.message(Command("start"))
async def start(message: types.Message):

    user = session.query(User).filter_by(
        telegram_id=str(message.from_user.id)
    ).first()

    if not user:

        role = "admin" if str(message.from_user.id) == str(ADMIN_ID) else "worker"

        user = User(
            telegram_id=str(message.from_user.id),
            name=message.from_user.full_name,
            role=role
        )

        session.add(user)
        session.commit()

    await message.answer("Workflow System hazırdır 🚀")


@dp.message(Command("ranking"))
async def ranking(message: types.Message):

    leaderboard = generate_leaderboard(session)

    text = "🏆 RANKING\n\n"

    for i, (name, score) in enumerate(leaderboard, 1):
        text += f"{i}. {name} — {score} bal\n"

    await message.answer(text)

# ---------------- MAIN ---------------- #

async def main():
    print("Workflow System başladı...")

    create_reels_template(session)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_stage_deadlines, "interval", seconds=30)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(
        bot,
        skip_updates=True,
        allowed_updates=["message", "callback_query"]
    )

async def check_stage_deadlines():
    now = datetime.datetime.now()

    stages = session.query(Stage).filter(
        Stage.status == "active",
        Stage.completed_at == None
    ).all()

    for stage in stages:
        if stage.deadline and stage.deadline < now:

            await bot.send_message(
                int(stage.assigned_user),
                f"⚠️ '{stage.name}' mərhələsi gecikir!"
            )

            stage.status = "overdue"
            session.commit()

if __name__ == "__main__":
    asyncio.run(main())
