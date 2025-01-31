import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# دریافت توکن‌ها از متغیرهای محیطی
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
REPO_OWNER = os.environ.get("GITHUB_USERNAME")  # نام کاربری گیت‌هاب
REPO_NAME = os.environ.get("GITHUB_REPO")  # نام مخزن گیت‌هاب
BRANCH = "main"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("سلام! فایل موسیقی یا متنی بفرست تا در GitHub آپلود کنم.")

def upload_to_github(file_path, file_name):
    """آپلود فایل در گیت‌هاب"""
    with open(file_path, "rb") as f:
        content = f.read()

    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(api_url, headers=headers)
    sha = response.json().get("sha") if response.status_code == 200 else None

    data = {
        "message": f"Upload {file_name}",
        "content": content.encode("base64").decode("utf-8"),
        "branch": BRANCH
    }
    
    if sha:
        data["sha"] = sha

    response = requests.put(api_url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        return f"✅ فایل {file_name} با موفقیت آپلود شد!"
    else:
        return f"❌ خطا در آپلود فایل: {response.text}"

def handle_document(update: Update, context: CallbackContext) -> None:
    document = update.message.document
    file_id = document.file_id
    file_name = document.file_name

    file = context.bot.get_file(file_id)
    file_path = f"downloads/{file_name}"
    file.download(file_path)

    result = upload_to_github(file_path, file_name)
    
    update.message.reply_text(result)
    os.remove(file_path)

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
