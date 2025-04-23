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
COLOR_SUBIDA = 'blue'
COLOR_BAJADA = 'red'

market_colors = mpf.make_marketcolors(up=COLOR_SUBIDA, down=COLOR_BAJADA)
custom_style = mpf.make_mpf_style(
    base_mpf_style='nightclouds',
    marketcolors=market_colors,
    facecolor='black',
    edgecolor='white',
    figcolor='black',
    gridcolor='gray'
)

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
        print("❌ Símbolo no reconocido:", moneda)
        return None

    url = f"https://api.binance.com/api/v3/klines?symbol={simbolo}&interval=4h&limit=30"
    respuesta = requests.get(url)

    print("STATUS:", respuesta.status_code)
    print("RESPUESTA:", respuesta.text[:500])  # Limita la respuesta por si es muy larga

    try:
        datos = respuesta.json()
    except Exception as e:
        print("❌ Error al convertir a JSON:", e)
        return None

    if not datos:
        print("❌ Binance regresó lista vacía")
        return None

    try:
        df = pd.DataFrame(datos, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)

        print("✅ DataFrame creado:")
        print(df.head())

        return df[['open', 'high', 'low', 'close']]

    except Exception as e:
        print("❌ Error al procesar el DataFrame:", e)
        return None

# ======== Función para generar gráfico y guardarlo ========
def crear_grafico(df, moneda):
    if df.empty:
        print("⚠️ DataFrame vacío. No se puede generar gráfico.")
        return None

    nombre = f"{moneda.upper()}_grafico.png"
    df.index.name = 'Date'

    mpf.plot(df,
             type='candle',
             style=custom_style,
             title=moneda.upper(),
             ylabel='Precio (USD)',
             volume=False,
             savefig=dict(fname=nombre, dpi=100, bbox_inches='tight'),
             mav=(3, 5),
             tight_layout=True,
             figratio=(12, 6),
             datetime_format='%b %d %Hh',
             warn_too_much_data=10000,
             update_width_config=dict(candle_linewidth=1.0))

    return nombre

# ======== Análisis simple de tendencia ========
def sugerencia(df):
    if df.empty or len(df['close']) < 5:
        return "⚠️ No hay suficientes datos para dar una sugerencia en este momento."

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

        if df is None or df.empty or 'close' not in df.columns or df['close'].empty:
            msg.body("⚠️ No se pudo obtener el precio actual de esa criptomoneda. Intenta más tarde.")
        else:
            print("HEADERS:", df.columns)
            print("DATAFRAME LENGTH:", len(df))
            print(df.head())
            nombre = crear_grafico(df, encontrada)
            consejo = sugerencia(df)
            precio_actual = df['close'].iloc[-1]
            mensaje = f"💰 {encontrada.upper()}: ${precio_actual:.2f} USD\n\n{consejo}"
            msg.body(mensaje)
            msg.media(f"https://trading-bot-x624.onrender.com/static/{nombre}")
    else:
        msg.body("Hola 👋 Pregúntame por BTC, ETH, USDT o TrumpCoin y te mostraré precio + gráfica 📊")

    return str(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
