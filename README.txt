PASOS PARA INSTALAR Y USAR ESTE BOT EN RAILWAY:

1. Crea cuenta en https://railway.app

2. Pulsa en "New Project" > "Deploy from GitHub repo" o "Deploy from template"
   (Si subes el ZIP, primero descomprímelo y crea un nuevo repo en GitHub con estos archivos)

3. Asegúrate de que Railway detecte:
   - "Start Command" = `python main.py`
   - "requirements.txt" = Python packages

4. En Railway, ve a la pestaña "Variables" y añade:
   - Key: TELEGRAM_BOT_TOKEN
   - Value: (Tu token del bot de Telegram que te da @BotFather)

5. Pulsa en "Deploy". El bot estará activo tras unos segundos.

6. En Telegram, abre tu bot y envía `/start`. Luego tu ubicación. Usa los comandos `/pases`, `/iss`, etc.

¡Listo!
