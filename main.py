import sys
sys.stdout.flush()

from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import pandas as pd
import mplfinance as mpf

app = Flask(__name__, static_folder='static')

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

# ======== NUEVA FUNCIÓN: CoinGecko en lugar de Binance ========
def obtener_precios(moneda):
    simbolos = {
        'btc': 'bitcoin',
        'eth': 'ethereum',
        'usdt': 'tether'
        # 'trumpcoin': 'trumpcoin'  # No disponible en CoinGecko
    }

    id_moneda = simbolos.get(moneda.lower())
    if not id_moneda:
        print("❌ Moneda no válida")
        return None

    url = f"https://api.coingecko.com/api/v3/coins/{id_moneda}/market_chart?vs_currency=usd&days=5&interval=hourly"
    respuesta = requests.get(url)

    print("STATUS:", respuesta.status_code)
    if respuesta.status_code != 200:
        print("❌ Error al consultar CoinGecko:", respuesta.text)
        return None

    datos = respuesta.json()

    try:
        precios = datos['prices']
    except KeyError:
        print("❌ Formato inesperado en respuesta de CoinGecko")
        return None

    df = pd.DataFrame(precios, columns=['timestamp', 'close'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df['close'] = df['close'].astype(float)
    df['open'] = df['close'].shift(1).fillna(df['close'])
    df['high'] = df[['open', 'close']].max(axis=1)
    df['low'] = df[['open', 'close']].min(axis=1)

    return df[['open', 'high', 'low', 'close']]

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
             savefig=dict(fname=f"static/{nombre}", dpi=100, bbox_inches='tight'),
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
    sys.stdout.flush()

    response = MessagingResponse()
    msg = response.message()

    monedas = ['btc', 'eth', 'usdt']
    encontrada = next((m for m in monedas if m in incoming_msg), None)

    if encontrada:
        df = obtener_precios(encontrada)

        if df is None or df.empty:
            msg.body("⚠️ No se pudo obtener el precio actual de esa criptomoneda. Intenta más tarde.")
        else:
            nombre = crear_grafico(df, encontrada)
            consejo = sugerencia(df)
            precio_actual = df['close'].iloc[-1]
            mensaje = f"💰 {encontrada.upper()}: ${precio_actual:.2f} USD\n\n{consejo}"
            msg.body(mensaje)
            msg.media(f"https://trading-bot-x624.onrender.com/static/{nombre}")
    else:
        msg.body("Hola 👋 Pregúntame por BTC, ETH o USDT y te mostraré precio + gráfica 📊")

    return str(response)

# ======== Servidor local/render ========
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), use_reloader=False)
