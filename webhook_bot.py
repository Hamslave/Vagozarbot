import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, Dispatcher, CommandHandler, ContextTypes
from config import TOKEN

app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

@app.route('/')
def index():
    return "ربات واگذار اینجاست!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return 'ok'

# هندلرهای اصلی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات واگذار به وب‌هوک وصل شد.")

application.add_handler(CommandHandler("start", start))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
