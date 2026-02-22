import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from vr_workflow.models import Stage, ChecklistItem
from vr_workflow.services.template_service import create_reels_template, create_task_from_template
from vr_workflow.services.workflow_service import toggle_checklist_item

BOT_TOKEN = "8446148700:AAFpzUpbKoAAeKN9ureWY8YHkY9yctUbdkw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
init_db()


# ---------------- UI FUNCTION ---------------- #

async def send_stage_view(chat_id, stage_id):
    with session_scope() as session:
        stage = session.query(Stage).filter_by(id=stage_id).first()

        if not stage:
            await bot.send_message(chat_id, "Mərhələ tapılmadı")
            return

        items = list(stage.checklist_items)

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

    await send_stage_view(message.chat.id, stage_id)


# ---------------- TOGGLE CHECKLIST ---------------- #

@dp.callback_query()
async def handle_toggle(callback: types.CallbackQuery):

    item_id = int(callback.data.split("_")[1])

        )

    await callback.message.delete()
    await send_stage_view(callback.message.chat.id, stage_id)

# ---------------- MAIN ---------------- #

async def main():
    print("Workflow System başladı...")

    with session_scope() as session:
        create_reels_template(session)

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
