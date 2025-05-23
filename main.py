import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from skyfield.api import Topos, load
from datetime import datetime, timedelta
import requests
import os

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Cargar efemérides y TLEs
ts = load.timescale()
sat_urls = {
    "ISS": "https://celestrak.org/NORAD/elements/stations.txt",
    "NOAA": "https://celestrak.org/NORAD/elements/noaa.txt",
    "METEOR": "https://celestrak.org/NORAD/elements/weather.txt"
}
sats = {}

def update_tles():
    for key, url in sat_urls.items():
        lines = requests.get(url).text.strip().splitlines()
        for i in range(0, len(lines), 3):
            name, l1, l2 = lines[i:i+3]
            if key == "ISS" and "ISS" not in name:
                continue
            if key == "NOAA" and "NOAA" not in name:
                continue
            if key == "METEOR" and "METEOR" not in name.upper():
                continue
            sats[name.strip()] = load.tle(name, l1, l2)

update_tles()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btn = KeyboardButton("📍 Enviar ubicación", request_location=True)
    markup = ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "👋 Bienvenido. Envía tu ubicación y usa /pases, /iss, /noaa o /meteor para ver los próximos 10 pases.",
        reply_markup=markup
    )

user_locations = {}

def get_passes(satname, lat, lon, max_results=10):
    satellite = sats.get(satname)
    if not satellite:
        return [f"No se encontró el satélite: {satname}"]
    observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
    t0 = ts.now()
    passes = []
    for mins in range(0, 24*60, 1):
        t = t0 + timedelta(minutes=mins)
        alt, az, _ = (satellite - observer).at(t).altaz()
        if alt.degrees > 10:
            passes.append(t.utc_datetime())
        if len(passes) >= max_results:
            break
    results = []
    for dt in passes:
        results.append(f"🛰 {satname}\n📅 {dt.strftime('%d/%m/%Y')}\n⏰ {dt.strftime('%H:%M:%S UTC')}")
    return results if results else ["No hay pases visibles en las próximas 24h."]

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    user_locations[update.effective_user.id] = (loc.latitude, loc.longitude)
    await update.message.reply_text("📍 Ubicación guardada. Ahora puedes usar /pases, /iss, /noaa o /meteor.")

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE, filter_key=None):
    uid = update.effective_user.id
    if uid not in user_locations:
        await update.message.reply_text("Por favor, envíame tu ubicación primero.")
        return
    lat, lon = user_locations[uid]
    results = []
    for name in sats:
        if filter_key and filter_key not in name:
            continue
        results.extend(get_passes(name, lat, lon, max_results=10))
    results.sort()
    chunks = ["\n\n".join(results[i:i+5]) for i in range(0, len(results), 5)]
    for chunk in chunks:
        await update.message.reply_text(chunk)

async def pases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_command(update, context)

async def iss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_command(update, context, "ISS")

async def noaa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_command(update, context, "NOAA")

async def meteor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_command(update, context, "METEOR")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pases", pases))
app.add_handler(CommandHandler("iss", iss))
app.add_handler(CommandHandler("noaa", noaa))
app.add_handler(CommandHandler("meteor", meteor))
app.add_handler(MessageHandler(filters.LOCATION, location_handler))

if __name__ == "__main__":
    app.run_polling()
