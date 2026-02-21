import asyncio
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from vr_workflow.database import Base, engine, SessionLocal
from vr_workflow.models import Task, Stage, ChecklistItem, UserStats, User
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8446148700:AAFpzUpbKoAAeKN9ureWY8YHkY9yctUbdkw"
ADMIN_ID = 889375033  # öz ID-ni yaz
MONTAGE_USER_ID = 889375033  # test üçün eyni qoya bilərsən

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


session = SessionLocal()


# ---------------- COMMANDS ---------------- #


@dp.message(Command("create_task"))
async def create_task(message: types.Message):

    # TASK
    task = Task(title="Reels Çəkilişi")
    session.add(task)
    session.commit()

    # STAGE 1 – ÇƏKİLİŞ
    stage1 = Stage(
        task_id=task.id,
        name="Çəkiliş",
        assigned_user=str(message.from_user.id),
        status="active",
        started_at=datetime.datetime.now(),
        deadline=datetime.datetime.now() + datetime.timedelta(minutes=3)
    )
    session.add(stage1)
    session.commit()

    # STAGE 2 – MONTAJ
    stage2 = Stage(
        task_id=task.id,
        name="Montaj",
        assigned_user=str(MONTAGE_USER_ID),
        status="pending",
        deadline=datetime.datetime.now() + datetime.timedelta(minutes=5)
    )
    session.add(stage2)
    session.commit()

    # CHECKLIST – ÇƏKİLİŞ
    items = [
        "Ssenari hazırdır",
        "Məkan hazırdır",
        "Çəkiliş edildi"
    ]

    for text in items:
        session.add(ChecklistItem(stage_id=stage1.id, text=text))

    session.commit()

    await send_stage_view(message.chat.id, stage1.id)


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
    item = session.query(ChecklistItem).filter_by(id=item_id).first()

    item.completed = not item.completed
    session.commit()

    stage = session.query(Stage).filter_by(id=item.stage_id).first()

    # STAGE TAMAMDIR?
    items = session.query(ChecklistItem).filter_by(stage_id=stage.id).all()

    if all(i.completed for i in items):

        stage.status = "completed"
        stage.completed_at = datetime.datetime.now()
        session.commit()

        print("STAGE TAMAMLANDI:", stage.name)

        await bot.send_message(
            int(stage.assigned_user),
            f"✅ Sənin '{stage.name}' mərhələn tamamlandı"
        )

        # NÖVBƏTİ STAGE TAP
        next_stage = session.query(Stage).filter(
            Stage.task_id == stage.task_id,
            Stage.status == "pending"
        ).first()

        if next_stage:
            next_stage.status = "active"
            session.commit()

            # Montaj checklist əlavə edirik
            if next_stage.name == "Montaj":
                montage_items = [
                    "Montaj başladı",
                    "Montaj bitdi"
                ]
                for text in montage_items:
                    session.add(ChecklistItem(stage_id=next_stage.id, text=text))
                session.commit()

            await bot.send_message(
                int(next_stage.assigned_user),
                f"🎬 Yeni mərhələ başladı: {next_stage.name}"
            )

        else:
            # BÜTÜN STAGE-LƏR TAMAMDIR
            task = session.query(Task).filter_by(id=stage.task_id).first()
            task.status = "completed"
            session.commit()

            await bot.send_message(
                ADMIN_ID,
                f"🏁 Layihə tamamlandı: {task.title}"
            )

    await callback.message.delete()
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

    user_id = str(message.from_user.id)

    stages = session.query(Stage).filter(
        Stage.assigned_user == user_id,
        Stage.status == "completed"
    ).all()

    if not stages:
        await message.answer("Hələ tamamlanan mərhələ yoxdur.")
        return

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

    text = f"""
    👤 PROFİL

    ✅ Tamamlanan mərhələlər: {total}
    ⚠️ Gecikən mərhələlər: {late_count}
    ⏱ Orta icra müddəti: {avg_minutes} dəqiqə
    🏆 Performance balı: {score}
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

    users = session.query(User).all()
    leaderboard = []

    for user in users:

        stages = session.query(Stage).filter(
            Stage.assigned_user == user.telegram_id,
            Stage.status == "completed"
        ).all()

        total = len(stages)
        late_count = 0

        for stage in stages:
            if stage.deadline and stage.completed_at:
                if stage.completed_at > stage.deadline:
                    late_count += 1

        score = total * 10 - late_count * 3

        leaderboard.append((user.name, score))

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    text = "🏆 RANKING\n\n"

    for i, (name, score) in enumerate(leaderboard, 1):
        text += f"{i}. {name} — {score} bal\n"

    await message.answer(text)

# ---------------- MAIN ---------------- #

async def main():
    print("Workflow System başladı...")

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
