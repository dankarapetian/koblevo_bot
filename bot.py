import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.ext import CallbackContext
from fastapi import FastAPI, Request
import uvicorn

from telegram.ext import AIORateLimiter

# Этапы разговора
NAME, SURNAME, WINE_TYPE, CONFIRM_ORDER, CITY, POST_OFFICE = range(6)

# Клавиатура для выбора вида вина
wine_keyboard = [["На розлив", "Бутылочное", "Оба"]]
wine_markup = ReplyKeyboardMarkup(wine_keyboard, one_time_keyboard=True, resize_keyboard=True)

# FastAPI-приложение
app = FastAPI()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

telegram_app = ApplicationBuilder().token(BOT_TOKEN).rate_limiter(AIORateLimiter()).build()

# Хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Как вас зовут?")
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
        f"Новый заказ:\n\n"
        f"Имя: {data['name']}\n"
        f"Фамилия: {data['surname']}\n"
        f"Вид вина: {data['wine_type']}\n"
        f"Это весь заказ: {data['order_confirmed']}\n"
        f"Город: {data['city']}\n"
        f"Новая Почта и улица: {data['post_office']}"
    )

    # Ответ клиенту
    await update.message.reply_text("Ваш заказ принят! Спасибо!")

    # Отправка владельцу
    admin_chat_id = 5511981632
    await context.bot.send_message(chat_id=admin_chat_id, text=summary)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заказ отменён.")
    return ConversationHandler.END

# Хендлеры
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

telegram_app.add_handler(conv_handler)

# Webhook endpoint
@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# Устанавливаем webhook при запуске
@app.on_event("startup")
async def on_startup():
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
