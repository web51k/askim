import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent
)

# ========= НАСТРОЙКИ =========
BOT_TOKEN = "8045079944:AAFBHTQ336b6R_lcnxho3Soq97ztFwZV65A"

NEWS_CHANNEL = "@vudik_conventor"
STARS_RATE_USD = 0.0118

CRYPTO = ["btc", "eth", "ton", "usdt", "sol"]
FIAT = ["usd", "kzt", "rub", "eur"]
ALL = CRYPTO + FIAT + ["stars"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ========= ВСПОМОГАТЕЛЬНОЕ =========
def parse(text: str):
    text = text.lower().replace(" ", "")
    m = re.match(r"([\d.]+)([a-z]{3,6})([a-z]{3,6})", text)
    if not m:
        return None
    return float(m.group(1)), m.group(2), m.group(3)

def fiat_rate(frm, to):
    url = f"https://api.exchangerate.host/convert?from={frm.upper()}&to={to.upper()}"
    r = requests.get(url, timeout=5).json()
    return r["result"]

def crypto_price_usd(symbol):
    url = "https://api.coingecko.com/api/v3/simple/price"
    r = requests.get(url, params={
        "ids": symbol,
        "vs_currencies": "usd"
    }, timeout=5).json()
    return r[symbol]["usd"]

CRYPTO_ID = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "ton": "the-open-network",
    "usdt": "tether",
    "sol": "solana"
}

def convert(amount, frm, to):
    if frm == "stars":
        usd = amount * STARS_RATE_USD
    elif frm in FIAT:
        usd = amount / fiat_rate("usd", frm)
    else:
        usd = amount * crypto_price_usd(CRYPTO_ID[frm])

    if to == "stars":
        return usd / STARS_RATE_USD
    elif to in FIAT:
        return usd * fiat_rate("usd", to)
    else:
        return usd / crypto_price_usd(CRYPTO_ID[to])

# ========= КНОПКИ =========
menu = InlineKeyboardMarkup(row_width=1)
menu.add(
    InlineKeyboardButton("💱 Как пользоваться", callback_data="help"),
    InlineKeyboardButton("💖 Донат", callback_data="donate"),
    InlineKeyboardButton("📢 Новости", url=f"https://t.me/{NEWS_CHANNEL.replace('@','')}")
)

# ========= /start =========
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer(
        "👋 Йо, братан!\n"
        "Я конвертирую крипту, валюты и Telegram Stars 💱\n\n"
        "Примеры:\n"
        "20USDT KZT\n"
        "5.4TON USD\n"
        "7USD RUB\n"
        "100STARS KZT\n\n"
        "Результат:\n"
        "20 USDT ≈ 9560 KZT",
        reply_markup=menu
    )

# ========= КНОПКИ =========
@dp.callback_query_handler(lambda c: c.data == "help")
async def help_cb(c: types.CallbackQuery):
    await c.message.answer(
        "📘 Как пользоваться\n\n"
        "Просто напиши:\n"
        "20USDT KZT\n"
        "5TON USD\n"
        "7USD RUB\n"
        "100STARS KZT\n\n"
        "Inline тоже работает:\n"
        "@BotName 10USDT KZT"
    )

@dp.callback_query_handler(lambda c: c.data == "donate")
async def donate_cb(c: types.CallbackQuery):
    await c.message.answer(
        "💖 Донат\n\n"
        "TON - UQCI8QvvgTvg0Az3GxNQLanVvSaoFT7nVyBJimjA1W8w4_1y\n\n"
        "Поддержка подарочком — @MrVudik ⭐"
    )

# ========= Обычные сообщения =========
@dp.message_handler()
async def convert_msg(msg: types.Message):
    parsed = parse(msg.text)
    if not parsed:
        return

    amount, frm, to = parsed
    if frm not in ALL or to not in ALL:
        return

    try:
        res = convert(amount, frm, to)
        await msg.answer(f"{amount} {frm.upper()} ≈ {res:.2f} {to.upper()}")
    except:
        await msg.answer("❌ Ошибка получения курса")

# ========= INLINE =========
@dp.inline_handler()
async def inline(q: types.InlineQuery):
    parsed = parse(q.query)
    if not parsed:
        return

    amount, frm, to = parsed
    if frm not in ALL or to not in ALL:
        return

    try:
        res = convert(amount, frm, to)
        text = f"{amount} {frm.upper()} ≈ {res:.2f} {to.upper()}"

        await q.answer([
            InlineQueryResultArticle(
                id="1",
                title=text,
                input_message_content=InputTextMessageContent(text)
            )
        ], cache_time=5)
    except:
        pass

# ========= ЗАПУСК =========
if __name__ == "__main__":
    print("Bot started")
    executor.start_polling(dp, skip_updates=True)