from telegram.ext import ApplicationBuilder
import handlers
import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv('API_TELEGRAM_TOKEN')

def main():
    engine=ApplicationBuilder().token(BOT_TOKEN).build()
    handlers.register(engine)
    engine.run_polling()
    