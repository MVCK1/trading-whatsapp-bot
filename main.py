
from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    from twilio.twiml.messaging_response import MessagingResponse

    incoming_msg = request.form.get('Body', '').lower()
    sender = request.form.get('From', '')

    print(f"Mensaje de {sender}: {incoming_msg}")

    # Crear respuesta automática
    response = MessagingResponse()
    msg = response.message()

    # Respuesta de prueba
    if 'eth' in incoming_msg:
        msg.body("El precio del ETH está en análisis 📊. Pronto te diré si es buen momento para comprar o vender.")
    else:
        msg.body("Hola 👋 Soy tu asistente crypto. Pregúntame por una moneda (como BTC, ETH o TrumpCoin).")

    return str(response), 200
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
