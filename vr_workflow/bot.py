import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from vr_workflow.models import Stage, ChecklistItem, Task
from vr_workflow.services.template_service import create_reels_template, create_task_from_template
from vr_workflow.services.workflow_service import toggle_checklist_item
from vr_workflow.database import init_db, session_scope

BOT_TOKEN = "8446148700:AAFpzUpbKoAAeKN9ureWY8YHkY9yctUbdkw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
init_db()


# ---------------- UI FUNCTION ---------------- #

async def send_stage_view(stage_id):
    with session_scope() as session:
        stage = session.query(Stage).filter_by(id=stage_id).first()

        if not stage:
            return None, None

        checklist_items = session.query(ChecklistItem).filter_by(stage_id=stage.id).all()

        keyboard = []

        if stage.status == "active":
            status_emoji = "🟢 ACTIVE"
        elif stage.status == "completed":
            status_emoji = "✅ COMPLETED"
        elif stage.status == "pending":
            status_emoji = "⏳ PENDING"
        else:
            status_emoji = stage.status

        deadline_text = stage.deadline.strftime("%d %b %H:%M") if stage.deadline else "Yoxdur"

        text = (
            f"📌 Stage: {stage.name}\n\n"
            f"Status: {status_emoji}\n"
            f"Revision: {stage.revision_count or 0}\n"
            f"Deadline: {deadline_text}\n\n"
        )

        for item in checklist_items:
            status = "✅" if item.completed else "⬜"
            text += f"{status} {item.text}\n"

            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status} {item.text}",
                    callback_data=f"toggle_{item.id}"
                )
            ])

        if stage.task.status == "waiting_approval":
            keyboard.append([
                InlineKeyboardButton(
                    text="✅ Task Təsdiqlə",
                    callback_data=f"approve_task_{stage.task.id}"
                )
            ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return text, markup

# ---------------- CREATE TASK COMMAND ---------------- #

@dp.message(Command("create_task"))
async def create_task_handler(message: types.Message):
    with session_scope() as session:
        stage_id = create_task_from_template(
            session,
            "Reels Production",
            message.from_user.id,
            message.from_user.id
        )

    text, markup = await send_stage_view(stage_id)
    await message.answer(text, reply_markup=markup)


# ---------------- TOGGLE CHECKLIST ---------------- #

@dp.callback_query()
async def handle_toggle(callback: types.CallbackQuery):
    if not callback.data or not callback.data.startswith("toggle_"):
        await callback.answer("Yanlış callback məlumatı", show_alert=True)
        return

    item_id = int(callback.data.split("_")[1])

    with session_scope() as session:
        stage_id = toggle_checklist_item(session, item_id)

    await callback.answer("Yeniləndi ✅")

    text, markup = await send_stage_view(stage_id)
    await callback.message.edit_text(text, reply_markup=markup)


@dp.callback_query()
async def handle_task_approve(callback: types.CallbackQuery):
    if not callback.data.startswith("approve_task_"):
        return

    task_id = int(callback.data.split("_")[2])

    with session_scope() as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if task:
            task.status = "approved"

    await callback.answer("Task təsdiqləndi 🎉")

    # Son stage-i göstər
    with session_scope() as session:
        last_stage = session.query(Stage)\
            .filter_by(task_id=task_id)\
            .order_by(Stage.order.desc())\
            .first()

        if not last_stage:
            return

    text, markup = await send_stage_view(last_stage.id)
    await callback.message.edit_text(text, reply_markup=markup)

# ---------------- MAIN ---------------- #

async def main():
    print("Workflow System başladı...")

    with session_scope() as session:
        create_reels_template(session)

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
