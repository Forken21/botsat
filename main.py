import logging
import requests
from skyfield.api import Loader, Topos, EarthSatellite
from datetime import datetime, timedelta
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Cargar satélites desde Celestrak
load = Loader('./data')
ts = load.timescale()
SATELLITE_GROUPS = {
    'iss': ['ISS (ZARYA)'],
    'noaa': ['NOAA 15', 'NOAA 18', 'NOAA 19'],
    'meteor': ['METEOR-M 2'],
}

def update_tles():
    response = requests.get('https://celestrak.com/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle')
    tle_lines = response.text.strip().splitlines()
    sats = {}
    for i in range(0, len(tle_lines), 3):
        name, l1, l2 = tle_lines[i:i+3]
        sats[name.strip()] = EarthSatellite(l1, l2, name.strip(), ts)
    return sats

sats = update_tles()

# Logging
logging.basicConfig(level=logging.INFO)

# Usuarios y ubicaciones
user_locations = {}

# Encuentra próximos pases visibles
def find_passes(sat, location, count=10):
    observer = Topos(latitude_degrees=location[0], longitude_degrees=location[1])
    now = ts.now()
    passes = []
    t0 = now
    while len(passes) < count:
        t1 = t0 + timedelta(days=1)
        times, events = sat.find_events(observer, t0, t1, altitude_degrees=10.0)
        for ti, event in zip(times, events):
            if event == 0:  # Only rising events
                passes.append(ti.utc_datetime())
                if len(passes) >= count:
                    break
        t0 = t1
    return passes

# Mostrar los pases
def format_passes(name, passes):
    msg = f"📡 Próximos pases visibles de {name}:\n"
    for dt in passes:
        local = dt + timedelta(hours=2)  # Ajuste horario
        msg += f"🕒 {local.strftime('%d-%m-%Y %H:%M:%S')}\n"
    return msg

# Comandos de Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton("📍 Enviar ubicación", request_location=True)]]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("¡Hola! Envíame tu ubicación para empezar.", reply_markup=markup)

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    user_locations[update.effective_user.id] = (loc.latitude, loc.longitude)
    await update.message.reply_text("📍 ¡Ubicación recibida! Ahora puedes pedir los pases con /iss /noaa /meteor o /pases.")

async def send_passes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_locations:
        await update.message.reply_text("Por favor, primero envíame tu ubicación con /start.")
        return

    location = user_locations[uid]
    group = update.message.text[1:]  # remove slash
    if group == "pases":
        groups = ["iss", "noaa", "meteor"]
    else:
        groups = [group]

    response = ""
    for g in groups:
        for name in SATELLITE_GROUPS.get(g, []):
            if name in sats:
                sat = sats[name]
                pases = find_passes(sat, location, count=10)
                response += format_passes(name, pases) + "\n"
            else:
                response += f"No se encontró el satélite {name}.\n"

    await update.message.reply_text(response.strip())

# Configurar bot
def main():
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["iss", "noaa", "meteor", "pases"], send_passes))
    app.add_handler(MessageHandler(filters.LOCATION, location))

    print("Bot funcionando...")
    app.run_polling()

if __name__ == "__main__":
    main()
