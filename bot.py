import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

keyboard = [
    ["📦 Посилка без Нової пошти", "📦 Посилка з Новою поштою"],
    ["📄 Документи"]
]

markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚚 BVexpress\n\n"
        "Калькулятор вартості доставки 🇩🇪➡️🇺🇦\n\n"
        "Оберіть тип відправлення:",
        reply_markup=markup
    )


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📦 Посилка без Нової пошти":
        context.user_data["price"] = 1.0
        await update.message.reply_text(
            "⚖️ Введіть вагу посилки в кг.\nНаприклад: 12"
        )

    elif text == "📦 Посилка з Новою поштою":
        context.user_data["price"] = 1.5
        await update.message.reply_text(
            "⚖️ Введіть вагу посилки в кг.\nНаприклад: 12"
        )

    elif text == "📄 Документи":
        await update.message.reply_text(
            "📄 Вартість доставки документів: 10 €",
            reply_markup=markup
        )

    elif "price" in context.user_data:
        try:
            weight = float(text.replace(",", "."))
            price_per_kg = context.user_data["price"]

            # Мінімальна вартість до 7 кг — 10 €
            if weight <= 7:
                total = 10
            else:
                total = weight * price_per_kg

            await update.message.reply_text(
                f"⚖️ Вага: {weight:g} кг\n"
                f"💶 Вартість: {total:g} €\n\n"
                "BVexpress 🇩🇪➡️🇺🇦",
                reply_markup=markup
            )

            context.user_data.pop("price", None)

        except ValueError:
            await update.message.reply_text(
                "Будь ласка, введіть вагу цифрами.\nНаприклад: 12"
            )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

    app.run_polling()


if __name__ == "__main__":
    main()
