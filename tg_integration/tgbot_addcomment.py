import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

TELEGRAM_TOKEN = "7025976523:AAGYPV3GDNMTx7wwJtwAZuyOWgvai-M2vNE"
TRACKER_TOKEN = "y0__xDX8rD7Axie6zQgvOuFkxLUi6NzfSchRjxRhiap2xaK6FrMqA"
TRACKER_ORG_ID = "bpfbu7h2q3i8e83avh49"
TRACKER_API_URL = "https://api.tracker.yandex.net/v3/issues/"

TRACKER_HEADERS = {
    "Authorization": f"OAuth {TRACKER_TOKEN}",
    "X-Cloud-Org-Id": TRACKER_ORG_ID,
    "Content-Type": "application/json",
}

GET_TASK_KEY, USE_TASK_KEY = range(2)


async def key_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправь мне ключ задачи, в которой нужно оставить комментарий"
    )
    return GET_TASK_KEY


async def get_user_task_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_task_key = update.message.text.strip()  

    if "-" not in user_task_key or len(user_task_key.split("-")) != 2:
        await update.message.reply_text(
            "❌ Неверный формат ключа задачи. Используйте формат TEST-123"
        )
        return ConversationHandler.END

    try:
        response = requests.get(TRACKER_API_URL, headers=TRACKER_HEADERS)

        if response.status_code != 200:
            error_msg = {
                404: "Задача не найдена",
                403: "Нет доступа к задаче",
                401: "Не авторизован",
            }.get(response.status_code, f"{response.status_code}")

            await update.message.reply_text(f"❌Проверьте ключ задачи")
            return ConversationHandler.END

        context.user_data["stored_key"] = user_task_key
        await update.message.reply_text(
            f"✅ Задача {user_task_key} найдена. Введите текст комментария:"
        )
        return USE_TASK_KEY

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при проверке задачи: {str(e)}")
        return ConversationHandler.END


async def use_task_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text_markdown_v2

    messageid = update.message.link
    user_task_key = context.user_data["stored_key"]
    issue_url_api = f"https://api.tracker.yandex.net/v3/issues/{user_task_key}/comments"

    payload = {"text": f"Комментарий добавлен из {messageid}\n\n{user_text}"}

    try:
        response = requests.post(issue_url_api, headers=TRACKER_HEADERS, json=payload)
        response.raise_for_status()

        issue_data = response.json()
        comment_id = f"https://tracker.yandex.ru/{user_task_key}#{issue_data['longId']}"

        await update.message.reply_text(
            f"✅ Комментарий добавлен!\nСсылка: {comment_id}"
        )
        return ConversationHandler.END

    except requests.exceptions.RequestException as e:
        error_msg = f"❌Ошибка при комментаровании задачи: {str(e)}"
        if hasattr(e, "response") and e.response.text:
            error_msg += f"\nДетали: {e.response.text}"
        await update.message.reply_text(error_msg)
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫Отмена")
    return ConversationHandler.END


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("comment", key_task)],
        states={
            GET_TASK_KEY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_task_key)
            ],
            USE_TASK_KEY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, use_task_key)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
