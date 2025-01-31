import os
import requests
import logging
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# بارگذاری مقادیر از فایل .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "rzarisfi"
REPO_NAME = "HarfsMusic"
BRANCH = "main"

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)

# دریافت لیست پوشه‌ها از گیت‌هاب
def fetch_folders():
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        folders = [item["path"] for item in response.json() if item["type"] == "dir"]
        return folders
    else:
        logger.error(f"Failed to fetch folders: {response.text}")
        return []

# ذخیره و آپلود فایل در GitHub
def upload_to_github(file_path, content, message="Upload file"):
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    
    data = {
        "message": message,
        "content": content,
        "branch": BRANCH
    }
    
    response = requests.put(api_url, json=data, headers=headers)
    return response.status_code == 201

# کنترل پیام‌های ارسالی توسط کاربر
def start(update: Update, context: CallbackContext) -> None:
    folders = fetch_folders()
    folder_list = "\n".join([f"- {folder}" for folder in folders]) if folders else "هیچ پوشه‌ای یافت نشد."
    update.message.reply_text(f"سلام! لطفاً یک فایل موسیقی یا متن ارسال کنید.\nپوشه‌های موجود:\n{folder_list}")

# پردازش فایل‌های دریافت‌شده
def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document or update.message.audio
    if not file:
        update.message.reply_text("لطفاً یک فایل معتبر ارسال کنید.")
        return

    # دریافت اطلاعات فایل
    file_id = file.file_id
    file_name = file.file_name
    folder_choice = "UploadedFiles"  # پوشه‌ای که فایل در آن ذخیره خواهد شد

    # دانلود فایل از تلگرام
    file_obj = context.bot.get_file(file_id)
    file_path = f"/tmp/{file_name}"
    file_obj.download(file_path)

    # تبدیل فایل به Base64 برای آپلود در گیت‌هاب
    with open(file_path, "rb") as f:
        content = f.read().encode("base64").decode()

    github_path = f"{folder_choice}/{file_name}"
    upload_success = upload_to_github(github_path, content)

    if upload_success:
        update.message.reply_text(f"✅ فایل {file_name} با موفقیت در گیت‌هاب آپلود شد.")
    else:
        update.message.reply_text("❌ خطا در آپلود فایل.")

# تنظیم و اجرای بات
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document | Filters.audio, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
