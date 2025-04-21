
from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot de trading activo 😎'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # Aquí iría la lógica para procesar mensajes de WhatsApp con Twilio y responder
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
