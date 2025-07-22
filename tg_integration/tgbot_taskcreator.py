from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from yandex_tracker_client import TrackerClient

TELEGRAM_TOKEN = "7025976523:AAGYPV3GDNMTx7wwJtwAZuyOWgvai-M2vNE"
TRACKER_TOKEN = "y0__xDX8rD7Axie6zQgvOuFkxLUi6NzfSchRjxRhiap2xaK6FrMqA"
TRACKER_ORG_ID = "bpfbu7h2q3i8e83avh49"

client = TrackerClient(token=TRACKER_TOKEN, cloud_org_id=TRACKER_ORG_ID)

TASK_NAME, TASK_DESCRIPTION, TASK_QUEUE = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название задачи")
    return TASK_NAME


async def task_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer1"] = update.message.text
    await update.message.reply_text("Введи описание задачи")
    return TASK_DESCRIPTION


async def task_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer2"] = update.message.text
    await update.message.reply_text("Введи название очереди")
    return TASK_QUEUE


async def create_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer3"] = update.message.text
    user = update.message.from_user
    username = user.username
    try:
        issue = client.issues.create(
            queue=context.user_data["answer3"],
            summary=context.user_data["answer1"],
            description=context.user_data["answer2"],
            author=username,
            followers=username
        )
        response = f"✅ Задача создана!\nСсылка: https://tracker.yandex.ru/{issue.key}"
    except Exception as e:
        response = f"❌ Ошибка: {str(e)}"

    await update.message.reply_text(response)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫Отмена")
    return ConversationHandler.END


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("create", start)],
        states={
            TASK_NAME:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, task_name)],
            TASK_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               task_description)
            ],
            TASK_QUEUE:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, create_task)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
