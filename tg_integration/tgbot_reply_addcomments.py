import requests
import re
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

TELEGRAM_TOKEN = "bot_token"
TRACKER_TOKEN = "oauth_token"
TRACKER_ORG_ID = "org_id"
TRACKER_API_URL = "https://api.tracker.yandex.net/v3/issues/"

TRACKER_HEADERS = {
    "Authorization": f"OAuth {TRACKER_TOKEN}",
    "X-Cloud-Org-Id": TRACKER_ORG_ID,
    "Content-Type": "application/json",
}


async def extract_from_last_line(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        await update.message.reply_text("Нет текста")
        return None

    text = update.message.reply_to_message.text
    lines = text.splitlines()

    if not lines:
        await update.message.reply_text("Не найдено ни одной строки!")
        return None

    last_line = lines[-1]
    match = re.search(r"\s+([A-Z0-9-]+)", last_line)

    if match:
        task_code = match.group(1)
        context.user_data["task_key"] = task_code
        return task_code
    else:
        await update.message.reply_text("Ключ задачи не найден")
        return None


async def add_comment_in_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_key = context.user_data.get("task_key")

    if not task_key:
        await update.message.reply_text("Ошибка: не найден ключ задачи")
        return ConversationHandler.END

    user_text = update.message.text_markdown_v2
    messageid = update.message.link
    issue_url_api = f"https://api.tracker.yandex.net/v3/issues/{task_key}/comments"

    payload = {"text": f"Комментарий добавлен из {messageid}\n\n{user_text}"}

    try:
        response = requests.post(issue_url_api, headers=TRACKER_HEADERS, json=payload)
        response.raise_for_status()  # ошибки

        issue_data = response.json()
        comment_id = f"https://tracker.yandex.ru/{task_key}#{issue_data['longId']}"

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


async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сначала извлекаем task_key
    task_key = await extract_from_last_line(update, context)

    if task_key:
        # Затем обрабатываем комментарий
        await add_comment_in_task(update, context)


if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply))

    print("Бот запущен...")
    app.run_polling()
