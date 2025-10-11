import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Включаем логирование, чтобы видеть ошибки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# --- Данные для справочника (можно расширять) ---
INFO_DATA = {
    "about": "Мы — супер-компания 'BotMakers' 🤖. Создаем лучших ботов для ваших задач. "
             "Наша миссия — автоматизировать рутину и делать жизнь проще!",
    "contacts": "📞 Связаться с нами:\n\n"
                "Email: support@botmakers.dev\n"
                "Телефон: +1 (234) 567-89-00\n"
                "Наш офис: Интернет, где-то в облаках ☁️",
    "web_dev": "🌐 Веб-разработка:\n\nСоздаем быстрые, адаптивные и красивые сайты. "
               "Используем современные технологии, чтобы ваш бизнес блистал в сети. "
               "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "mobile_dev": "📱 Мобильная разработка:\n\nРазрабатываем нативные приложения для iOS и Android. "
                  "Ваши идеи в кармане у каждого клиента. "
                  "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
}

# --- Определяем клавиатуры ---

# Главное меню
main_menu_keyboard = [
    [KeyboardButton("О нас ℹ️"), KeyboardButton("Услуги 🛠️")],
    [KeyboardButton("Контакты 📞")]
]
main_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)

# Меню услуг
services_menu_keyboard = [
    [KeyboardButton("Веб-разработка 🌐"), KeyboardButton("Мобильная разработка 📱")],
    [KeyboardButton("Назад ⬅️")]
]
services_markup = ReplyKeyboardMarkup(services_menu_keyboard, resize_keyboard=True)


# --- Функции-обработчики (хендлеры) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и главное меню при команде /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\n\nЯ бот-справочник. Выбери раздел в меню ниже, чтобы узнать информацию.",
        reply_markup=main_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия кнопок меню."""
    text = update.message.text

    # Роутер по кнопкам
    if text == "О нас ℹ️":
        await update.message.reply_text(INFO_DATA["about"], reply_markup=main_markup)

    elif text == "Контакты 📞":
        await update.message.reply_text(INFO_DATA["contacts"], reply_markup=main_markup)

    elif text == "Услуги 🛠️":
        await update.message.reply_text("Выберите тип услуг:", reply_markup=services_markup)

    elif text == "Веб-разработка 🌐":
        await update.message.reply_text(INFO_DATA["web_dev"], reply_markup=services_markup)

    elif text == "Мобильная разработка 📱":
        await update.message.reply_text(INFO_DATA["mobile_dev"], reply_markup=services_markup)

    elif text == "Назад ⬅️":
        await update.message.reply_text("Вы вернулись в главное меню.", reply_markup=main_markup)

    else:
        await update.message.reply_text("Извините, я не понимаю эту команду. Пожалуйста, используйте кнопки меню.")


def main() -> None:
    """Основная функция для запуска бота."""
    TOKEN = '8307944503:AAHs4-YdnUNox56ZPqwjC1raMD1zdcTMsCQ'

    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота (он будет работать, пока не остановишь процесс)
    logger.info("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()