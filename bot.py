from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# Этапы диалога
NAME, SURNAME, WINE_TYPE, CONFIRM_ORDER, CITY, POST_OFFICE = range(6)

# Клавиатура для выбора вида вина
wine_keyboard = [["На розлив", "Бутылочное", "Оба"]]
wine_markup = ReplyKeyboardMarkup(wine_keyboard, one_time_keyboard=True, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Давайте оформим заказ.\n\nКак вас зовут?")
    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Отлично! А ваша фамилия?")
    return SURNAME


async def surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["surname"] = update.message.text
    await update.message.reply_text("Выберите вид вина:", reply_markup=wine_markup)
    return WINE_TYPE


async def wine_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["wine_type"] = update.message.text
    await update.message.reply_text("Это весь ваш заказ? (да/нет)")
    return CONFIRM_ORDER


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_confirmed"] = update.message.text
    await update.message.reply_text("Введите ваш город:")
    return CITY


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    await update.message.reply_text("Введите отделение Новой Почты и улицу:")
    return POST_OFFICE


async def post_office(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["post_office"] = update.message.text

    data = context.user_data
    summary = (
        f"Спасибо за заказ!\n\n"
        f"Имя: {data['name']}\n"
        f"Фамилия: {data['surname']}\n"
        f"Вид вина: {data['wine_type']}\n"
        f"Это весь заказ: {data['order_confirmed']}\n"
        f"Город: {data['city']}\n"
        f"Отделение НП и улица: {data['post_office']}"
    )

    await update.message.reply_text(summary)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заказ отменён.")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token("8031735761:AAHJQtX-5RdbN75TsFHZ_QmGwlA4k6QYcXs").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, surname)],
            WINE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wine_type)],
            CONFIRM_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            POST_OFFICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_office)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
