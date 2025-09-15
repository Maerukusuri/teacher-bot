from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
from datetime import datetime
import os
import logging
from telegram.error import NetworkError, TelegramError

# ----------------------------
# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ----------------------------
# Файл для сохранения вопросов
QUESTIONS_FILE = "questions.txt"

if not os.path.exists(QUESTIONS_FILE):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        f.write("=== Вопросы учителей ===\n\n")

# --------------------------
# Определяем язык (RU или ET)
def detect_language(text: str) -> str:
    if re.search(r"[а-яА-ЯёЁ]", text):
        return "ru"
    return "et"

# --------------------------
# Приветственное сообщение
async def send_welcome(update: Update, lang: str):
    if lang == "ru":
        welcome_text = (
            "👋 Привет! Я бот для учителей Тондираба.\n\n"
            "Меня зовут Тондик 😊\n"
            "Моя задача — собрать ваши вопросы, чтобы команда школы могла подготовить ответы "
            "и проанализировать, какие моменты вызывают трудности.\n\n"
            "⚠️ Обратите внимание: чтобы вопрос был сохранён в базу, он должен заканчиваться на знак вопроса (?)"
        )
    else:
        welcome_text = (
            "👋 Tere! Ma olen Tondiraba õpetajate bot.\n\n"
            "Minu nimi on Tondik 😊\n"
            "Minu ülesanne on koguda teie küsimusi, et kooli meeskond saaks ette valmistada vastused "
            "ja analüüsida, millised teemad on õpetajatele ebaselged.\n\n"
            "⚠️ Palun pange tähele: et küsimus salvestataks, peab see lõppema küsimärgiga (?)"
        )

    await update.message.reply_text(welcome_text)

# ----------------------------
# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lang = detect_language(text)

    # Приветствие
    if text.lower() in ["привет", "здравствуйте", "добрый день", "tere", "tsau", "hei"]:
        return await send_welcome(update, lang)

    # На вопрос "доколе?" бот отвечает картинкой
    if text.lower() == "доколе?":
        await update.message.reply_photo(
            photo="https://i.pinimg.com/736x/43/e5/b1/43e5b1b417419ca8a9ea0194cd5a62e2.jpg",
            caption="😅"
        )
        return

    # Сохраняем вопросы
    if text.endswith("?"):
        with open(QUESTIONS_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
                f"UserID {update.message.from_user.id} ({update.message.from_user.first_name}): {text}\n"
            )

        reply = "✅ Вопрос сохранён!" if lang == "ru" else "✅ Küsimus on salvestatud!"
    else:
        reply = (
            "⛔ Сейчас в мои функции входит сбор вопросов от учителей.\n"
            "Пожалуйста, сформулируйте сообщение в виде вопроса и завершите его знаком вопроса (?)."
            if lang == "ru"
            else
            "⛔ Praegu on minu ülesanne koguda õpetajatelt küsimusi.\n"
            "Palun sõnastage oma sõnum küsimusena ja lõpetage see küsimärgiga (?)."
        )

    await update.message.reply_text(reply)

# ----------------------------
# Команда для получения всех вопросов
async def get_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(QUESTIONS_FILE):
        await update.message.reply_text("❌ Файл с вопросами не найден.")
        return

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    for i in range(0, len(content), 4000):
        await update.message.reply_text(content[i:i+4000])

# ----------------------------
# Обработчик ошибок
async def handle_error(update, context):
    logging.error(f"Update {update} вызвал ошибку: {context.error}")
    if isinstance(context.error, NetworkError):
        logging.warning("⚠️ NetworkError: возможно временный сбой, повторная попытка...")
    elif isinstance(context.error, TelegramError):
        logging.warning("⚠️ TelegramError: проверьте токен или доступ к API")
    else:
        logging.warning(f"⚠️ Другая ошибка: {context.error}")

# ----------------------------
def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("❌ TELEGRAM_TOKEN не найден. Установите переменную окружения!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", lambda u, c: send_welcome(u, detect_language(u.message.text or ""))))
    app.add_handler(CommandHandler("getquestions", get_questions))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик ошибок
    app.add_error_handler(handle_error)

    print("🤖 Бот запущен... (polling)")
    app.run_polling()

# ----------------------------
if __name__ == "__main__":
    main()
