from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.form.get('Body', '').lower()
    sender = request.form.get('From', '')
    print(f"Mensaje de {sender}: {incoming_msg}")

    response = MessagingResponse()
    msg = response.message()

    if 'btc' in incoming_msg:
        msg.body("📈 BTC está en análisis. Pronto te diré si conviene comprar o vender con gráfico incluido.")
    elif 'eth' in incoming_msg:
        msg.body("📈 ETH está en análisis. Pronto te diré si conviene comprar o vender con gráfico incluido.")
    elif 'usdt' in incoming_msg:
        msg.body("📈 USDT está en análisis. Pronto te diré si conviene comprar o vender con gráfico incluido.")
    elif 'trumpcoin' in incoming_msg:
        msg.body("📈 TrumpCoin está en análisis. Pronto te diré si conviene comprar o vender con gráfico incluido.")
    elif 'test auto' in incoming_msg:
        msg.body("✅ Prueba recibida. El sistema automático está activo.")
    else:
        msg.body("Hola 👋 Pregúntame por una moneda (BTC, ETH, USDT o TrumpCoin).")

    return str(response), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host='0.0.0.0', port=port)
