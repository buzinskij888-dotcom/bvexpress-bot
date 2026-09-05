import os
from telegram import Update, ReplyKeyboardMarkup , InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📦 Посилка без Нової пошти", "📦 Посилка з Новою поштою"],
        ["📄 Документи"],
    ],
    resize_keyboard=True,
)

YES_NO_KEYBOARD = ReplyKeyboardMarkup(
    [["✅ Так", "❌ Ні"]],
    resize_keyboard=True,
)


def number(text):
    return float(text.replace(",", ".").strip())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🚚 BVexpress\n\n"
        "Калькулятор вартості доставки 🇩🇪➡️🇺🇦\n\n"
        "Оберіть тип відправлення:",
        reply_markup=MAIN_KEYBOARD,
    )


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # ГОЛОВНЕ МЕНЮ
    if text == "📄 Документи":
        context.user_data.clear()

        await update.message.reply_text(
            "📄 Вартість доставки документів: 10 €",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    if text == "📦 Посилка без Нової пошти":
        context.user_data.clear()
        context.user_data["rate"] = 1.0
        context.user_data["type"] = "Без Нової пошти"
        context.user_data["state"] = "weight"

        await update.message.reply_text(
            "⚖️ Вкажіть фактичну вагу посилки в кг.\n\n"
            "Наприклад: 8.5"
        )
        return

    if text == "📦 Посилка з Новою поштою":
        context.user_data.clear()
        context.user_data["rate"] = 1.5
        context.user_data["type"] = "З Новою поштою"
        context.user_data["state"] = "weight"

        await update.message.reply_text(
            "⚖️ Вкажіть фактичну вагу посилки в кг.\n\n"
            "Наприклад: 8.5"
        )
        return

    state = context.user_data.get("state")

    # ФАКТИЧНА ВАГА
    if state == "weight":
        try:
            weight = number(text)

            if weight <= 0:
                raise ValueError

            context.user_data["weight"] = weight
            context.user_data["state"] = "dimensions_question"

            await update.message.reply_text(
                "📐 Бажаєте врахувати розміри посилки та обʼємну вагу?",
                reply_markup=YES_NO_KEYBOARD,
            )

        except ValueError:
            await update.message.reply_text(
                "❗ Введіть вагу числом.\nНаприклад: 8.5"
            )
        return

    # ЧИ РАХУВАТИ ОБʼЄМНУ ВАГУ
    if state == "dimensions_question":

        if text == "✅ Так":
            context.user_data["state"] = "length"

            await update.message.reply_text(
                "📏 Вкажіть ДОВЖИНУ посилки в сантиметрах.\n\n"
                "Наприклад: 60"
            )
            return

        if text == "❌ Ні":
            await calculate(update, context, use_volume=False)
            return

        await update.message.reply_text(
            "Оберіть ✅ Так або ❌ Ні.",
            reply_markup=YES_NO_KEYBOARD,
        )
        return

    # ДОВЖИНА
    if state == "length":
        try:
            value = number(text)

            if value <= 0:
                raise ValueError

            context.user_data["length"] = value
            context.user_data["state"] = "width"

            await update.message.reply_text(
                "↔️ Вкажіть ШИРИНУ посилки в сантиметрах.\n\n"
                "Наприклад: 40"
            )

        except ValueError:
            await update.message.reply_text(
                "❗ Введіть довжину числом.\nНаприклад: 60"
            )
        return

    # ШИРИНА
    if state == "width":
        try:
            value = number(text)

            if value <= 0:
                raise ValueError

            context.user_data["width"] = value
            context.user_data["state"] = "height"

            await update.message.reply_text(
                "↕️ Вкажіть ВИСОТУ посилки в сантиметрах.\n\n"
                "Наприклад: 30"
            )

        except ValueError:
            await update.message.reply_text(
                "❗ Введіть ширину числом.\nНаприклад: 40"
            )
        return

    # ВИСОТА
    if state == "height":
        try:
            value = number(text)

            if value <= 0:
                raise ValueError

            context.user_data["height"] = value

            await calculate(update, context, use_volume=True)

        except ValueError:
            await update.message.reply_text(
                "❗ Введіть висоту числом.\nНаприклад: 30"
            )
        return

    await update.message.reply_text(
        "Оберіть тип відправлення:",
        reply_markup=MAIN_KEYBOARD,
    )


async def calculate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    use_volume: bool,
):
    actual_weight = context.user_data["weight"]
    rate = context.user_data["rate"]
    delivery_type = context.user_data["type"]

    if use_volume:
        length = context.user_data["length"]
        width = context.user_data["width"]
        height = context.user_data["height"]

        # Формула BVexpress:
        # Довжина × Ширина × Висота / 4000
        volume_weight = (length * width * height) / 4000

        chargeable_weight = max(actual_weight, volume_weight)

        price = max(10, chargeable_weight * rate)

        result = (
            "✅ РОЗРАХУНОК BVexpress\n\n"
            f"📦 Тип: {delivery_type}\n\n"
            f"⚖️ Фактична вага: {actual_weight:.2f} кг\n"
            f"📐 Розміри: {length:g} × {width:g} × {height:g} см\n"
            f"📊 Обʼємна вага: {volume_weight:.2f} кг\n\n"
            f"⚖️ Розрахункова вага: {chargeable_weight:.2f} кг\n"
            f"💶 Тариф: {rate:.2f} €/кг\n\n"
            f"💰 ВАРТІСТЬ ДОСТАВКИ: {price:.2f} €"
        )

    else:
        chargeable_weight = actual_weight
        price = max(10, chargeable_weight * rate)

        result = (
            "✅ РОЗРАХУНОК BVexpress\n\n"
            f"📦 Тип: {delivery_type}\n\n"
            f"⚖️ Вага: {actual_weight:.2f} кг\n"
            f"💶 Тариф: {rate:.2f} €/кг\n\n"
            f"💰 ВАРТІСТЬ ДОСТАВКИ: {price:.2f} €"
        )

    context.user_data.clear()

    await update.message.reply_text(
        result,
        reply_markup=MAIN_KEYBOARD,
    )

async def post_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🧮 Розрахувати доставку",
            url="https://t.me/BVexpress_calc_bot?start=channel"
        )]
    ])

    text = (
        "📦 РОЗРАХУНОК ВАРТОСТІ ДОСТАВКИ 🇩🇪➡️🇺🇦\n\n"
        "⚖️ Бот автоматично розрахує фактичну та обʼємну вагу.\n\n"
        "🚚 Без Нової пошти — 1 €/кг\n"
        "📮 З Новою поштою — 1,50 €/кг\n"
        "📦 Мінімальна вартість — 10 €\n"
        "📄 Документи — 10 €\n\n"
        "Натисніть кнопку нижче 👇"
    )

    await context.bot.send_message(
        chat_id="@BV_express_888",
        text=text,
        reply_markup=keyboard
    )
    await update.message.reply_text("✅ Кнопку опубліковано в каналі!")
def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не знайдено")

    app = Application.builder().token(TOKEN.strip()).build()

    app.add_handler(CommandHandler("start", start)) 
        app.add_handler(CommandHandler("post_channel", post_channel))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message)
    )

    print("BVexpress bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
