from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
from datetime import datetime
import os
import git  # для пуша в GitHub

# ----------------------------
# Файл для сохранения вопросов
QUESTIONS_FILE = "questions.txt"

# Проверяем, есть ли файл, если нет — создаём
if not os.path.exists(QUESTIONS_FILE):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        f.write("=== Вопросы учителей ===\n\n")

# ----------------------------
# Путь к репозиторию на сервере (Railway обычно /app)
REPO_PATH = "/app"
# Ссылка на GitHub с токеном из переменной окружения
GITHUB_URL = f"https://{os.getenv('GITHUB_TOKEN')}@github.com/<USERNAME>/<REPO>.git"

# ----------------------------
# Определяем язык (RU или ET)
def detect_language(text: str) -> str:
    if re.search(r"[а-яА-ЯёЁ]", text):
        return "ru"
    return "et"

# ----------------------------
# Приветственное сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    lang = detect_language(text)

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

    # Если это приветствие — показываем welcome
    if text.lower() in ["привет", "здравствуйте", "добрый день", "tere", "tsau", "hei"]:
        return await start(update, context)

    if text.endswith("?"):
        # Сохраняем вопрос с датой/временем и ID пользователя
        with open(QUESTIONS_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
                f"UserID {update.message.from_user.id} ({update.message.from_user.first_name}): {text}\n"
            )

        # --------- Пушим в GitHub ---------
        try:
            repo = git.Repo(REPO_PATH)
            repo.git.add(QUESTIONS_FILE)
            repo.index.commit(f"New question at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            origin = repo.remote(name='origin')
            origin.push()
            print("✅ Questions.txt pushed to GitHub")
        except Exception as e:
            print(f"❌ Ошибка при пуше в GitHub: {e}")
        # ----------------------------------

        if lang == "ru":
            reply = "✅ Вопрос сохранён и отправлен в GitHub!"
        else:
            reply = "✅ Küsimus salvestatud ja saadetud GitHub'i!"
    else:
        if lang == "ru":
            reply = (
                "⛔ Сейчас в мои функции входит сбор вопросов от учителей.\n"
                "Пожалуйста, сформулируйте сообщение в виде вопроса и завершите его знаком вопроса (?)."
            )
        else:
            reply = (
                "⛔ Praegu on minu ülesanne koguda õpetajatelt küsimusi.\n"
                "Palun sõnastage oma sõnum küsimusena ja lõpetage see küsimärgiga (?)."
            )

    await update.message.reply_text(reply)

# ----------------------------
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")  # <-- берём токен из переменной окружения
    if not TOKEN:
        raise ValueError("❌ TELEGRAM_TOKEN не найден. Установите переменную окружения!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен... (режим сбора вопросов)")
    app.run_polling()

# ----------------------------
if __name__ == "__main__":
    main()
