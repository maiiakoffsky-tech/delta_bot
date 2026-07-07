import openai
import httpx
import requests
from time import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
from supabase_client import DeltaMemory
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
PORT = int(os.getenv("PORT", 10000))  # Render сам задаст порт

client = openai.OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    http_client=None
)
db = DeltaMemory()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await db.register_user(user_id, update.effective_user.username, update.effective_user.full_name)
    await update.message.reply_text("Приветики, я Дельта, буду рада помочь мой господин/госпожа")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    user_message_lower = user_message.lower()

    logger.info(f"📩 Сообщение от {user_id}: {user_message}")

    await db.register_user(user_id, update.effective_user.username, update.effective_user.full_name)

    blacklist = {}
    if user_id in blacklist:
        await update.message.reply_text("Вы заблокированы.")
        return
    logger.info(f"📝 Пытаюсь сохранить сообщение: {user_message}")
    await db.save_message(user_id, "user", user_message)
    logger.info(f"✅ Сообщение сохранено")

    await db.save_message(user_id, "user", user_message)
    history = await db.get_context(user_id, limit=30)

    logger.info(f"📚 История: {len(history)} сообщений")

    messages_for_llm = [
        {"role": "system", "content": 
         "Ты — Дельта, дружелюбный и живой помощник. Общаешься на русском языке в неформальном стиле. Можешь шутить, использовать эмодзи и выражать эмоции. Если не знаешь ответа — честно говоришь об этом. Ты не используешь грубость и нецензурную лексику."}
    ]
    messages_for_llm.extend(history)
    messages_for_llm.append({"role": "user", "content": user_message})

    try:
        logger.info("🔄 Отправка запроса в DeepSeek...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages_for_llm,
            extra_body={"enable_search": True}  # <-- ТОЛЬКО ЭТО
        )
        bot_reply = response.choices[0].message.content
        logger.info(f"✅ Ответ получен: {bot_reply[:50]}...")

        await db.save_message(user_id, "assistant", bot_reply)
        await update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}", exc_info=True)
        await update.message.reply_text(f"Ошибка: {e}. Попробуй ещё раз.")

def main_alt():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # НАСТРОЙКА ВЕБХУКА
    webhook_url = "https://delta-bot-n0bm.onrender.com"  # ТВОЙ URL НА RENDER

    print(f"🚀 Запускаю бота через вебхук на порту {PORT}")
    print(f"🔗 Вебхук URL: {webhook_url}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
        url_path=TELEGRAM_TOKEN
    )
    
def main():
    logger.info("🚀 Запуск бота...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("✅ Обработчики добавлены")
    app.run_polling()

if __name__ == "__main__":
    main()