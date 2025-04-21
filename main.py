
from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Extraemos datos del formulario, no como JSON
    incoming_msg = request.form.get('Body', '').lower()
    sender = request.form.get('From', '')

    print(f"Mensaje de {sender}: {incoming_msg}")  # Para debug

    # Aquí podrías responder algo (por ahora, no respondemos nada)
    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
