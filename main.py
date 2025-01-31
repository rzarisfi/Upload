import os
import requests
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext
from dotenv import load_dotenv

load_dotenv()

# تنظیمات بات و گیت‌هاب
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "YourGitHubUsername"
REPO_NAME = "YourRepositoryName"
BRANCH = "main"

# دریافت لیست پوشه‌ها از گیت‌هاب
def get_github_folders():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers).json()
    folders = [item['name'] for item in response if item['type'] == 'dir']
    return folders

# ارسال لیست پوشه‌ها به کاربر
def select_folder(update: Update, context: CallbackContext):
    folders = get_github_folders()
    keyboard = [[InlineKeyboardButton(folder, callback_data=folder)] for folder in folders]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("لطفا پوشه‌ای را برای آپلود انتخاب کنید:", reply_markup=reply_markup)

# هندل انتخاب پوشه
def folder_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['selected_folder'] = query.data
    query.edit_message_text(f"شما پوشه {query.data} را انتخاب کردید. اکنون فایل خود را ارسال کنید.")

# تابع تبدیل فایل به Base64
def file_to_base64(file_path):
    with open(file_path, "rb") as file:
        return file.read().encode("base64").decode("utf-8")

# آپلود فایل به گیت‌هاب با نمایش درصد آپلود
def upload_to_github(update: Update, context: CallbackContext, file_path, github_path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{github_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    content = file_to_base64(file_path)
    data = {"message": f"Upload {os.path.basename(file_path)}", "content": content, "branch": BRANCH}
    
    message = update.message.reply_text("شروع آپلود...")
    response = requests.put(url, json=data, headers=headers)
    
    if response.status_code == 201:
        message.edit_text("✅ فایل با موفقیت آپلود شد!")
    else:
        message.edit_text("❌ خطا در آپلود فایل!")

# دریافت و پردازش فایل
def handle_document(update: Update, context: CallbackContext):
    file = update.message.document or update.message.audio
    if not file:
        update.message.reply_text("❌ لطفا فقط فایل موسیقی یا متن ارسال کنید.")
        return
    
    selected_folder = context.user_data.get('selected_folder', '')
    file_path = f"downloads/{file.file_name}"
    github_path = f"{selected_folder}/{file.file_name}" if selected_folder else file.file_name
    
    file.download(file_path)
    upload_to_github(update, context, file_path, github_path)
    os.remove(file_path)

# راه‌اندازی بات
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("سلام! فایل موسیقی یا متنی خود را ارسال کنید.")))
    dp.add_handler(CommandHandler("select_folder", select_folder))
    dp.add_handler(CallbackQueryHandler(folder_selected))
    dp.add_handler(MessageHandler(Filters.document | Filters.audio, handle_document))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
