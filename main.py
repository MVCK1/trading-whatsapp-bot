from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

app = Flask(__name__)

# ======== Configuración de colores para velas ========
custom_style = mpf.make_mpf_style(
    base_mpf_style='nightclouds',
    facecolor='black',
    edgecolor='white',
    figcolor='black',
    gridcolor='gray'
)

COLOR_SUBIDA = 'blue'
COLOR_BAJADA = 'red'

# ======== Función para obtener precios de Binance ========
def obtener_precios(moneda):
    simbolos = {
        'btc': 'BTCUSDT',
        'eth': 'ETHUSDT',
        'usdt': 'USDTUSDT',
        'trumpcoin': 'TRUMPUSDT'
    }
    simbolo = simbolos.get(moneda.lower())
    if not simbolo:
        return None

    url = f"https://api.binance.com/api/v3/klines?symbol={simbolo}&interval=4h&limit=30"
    respuesta = requests.get(url)
    datos = respuesta.json()

    df = pd.DataFrame(datos, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)

    return df[['open', 'high', 'low', 'close']]

# ======== Función para generar gráfico y guardarlo ========
def crear_grafico(df, moneda):
    if not os.path.exists("static"):
        os.makedirs("static")
    nombre = f"{moneda.upper()}_grafico.png"
    ruta = os.path.join("static", nombre)
    mpf.plot(df, type='candle', style=custom_style,
             title=f"{moneda.upper()} - Velas 4h",
             ylabel='Precio (USDT)',
             savefig=dict(fname=ruta, dpi=100, bbox_inches='tight'),
             mav=(3, 5),
             tight_layout=True,
             figratio=(12,6),
             volume=False,
             datetime_format='%b %d %Hh',
             warn_too_much_data=10000,
             update_width_config=dict(candle_linewidth=1.0),
             colorup=COLOR_SUBIDA, colordown=COLOR_BAJADA)
    return nombre

# ======== Análisis simple de tendencia ========
def sugerencia(df):
    ultimos = df['close'].iloc[-5:]
    if ultimos[-1] > ultimos.mean():
        return "📈 La tendencia parece alcista. Podría ser buen momento para comprar."
    else:
        return "📉 La tendencia parece bajista. Tal vez sea mejor esperar para comprar."

# ======== Webhook principal ========
@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.form.get('Body', '').lower()
    remitente = request.form.get('From', '')
    print(f"Mensaje de {remitente}: {incoming_msg}")

    response = MessagingResponse()
    msg = response.message()

    monedas = ['btc', 'eth', 'usdt', 'trumpcoin']
    encontrada = next((m for m in monedas if m in incoming_msg), None)

    if encontrada:
        df = obtener_precios(encontrada)
        if df is not None:
            nombre = crear_grafico(df, encontrada)
            consejo = sugerencia(df)
            precio_actual = df['close'].iloc[-1]
            mensaje = f"💰 {encontrada.upper()}: ${precio_actual:.2f} USD\n\n{consejo}"
            msg.body(mensaje)
            msg.media(f"https://trading-bot-x624.onrender.com/static/{nombre}")  # Reemplaza si usas carpeta /static
        else:
            msg.body("No pude obtener los datos en este momento.")
    else:
        msg.body("Hola 👋 Pregúntame por BTC, ETH, USDT o TrumpCoin y te mostraré precio + gráfica 📊")

    return str(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))