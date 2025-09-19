import os
from flask import Flask, jsonify, request
import secrets
from deposit import create_deposit
from database import add_transaction

app = Flask(__name__)

# Chave de API de teste
TEST_API_KEY = "sk_live_test_12345"

def require_api_key(f):
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "API key required"}), 401
        
        api_key = auth_header.replace("Bearer ", "")
        if api_key != TEST_API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route("/")
def home():
    return jsonify({
        "message": "Gateway PIX API está funcionando!",
        "status": "online",
        "version": "2.0",
        "endpoints": [
            "GET / - Status da API",
            "POST /api/v1/test - Teste com autenticação",
            "POST /api/v1/pix/deposit - Gerar PIX"
        ]
    })

@app.route("/api/v1/test", methods=["POST"])
@require_api_key
def test_auth():
    return jsonify({
        "message": "Autenticação funcionando!",
        "authenticated": True
    })

@app.route("/api/v1/pix/deposit", methods=["POST"])
@require_api_key
def generate_pix():
    data = request.get_json()
    if not data or "amount" not in data or "description" not in data:
        return jsonify({"error": "Amount and description are required"}), 400

    amount = data["amount"]
    description = data["description"]

    try:
        # Obtenha o token de autenticação da requisição
        auth_header = request.headers.get("Authorization")
        token = auth_header.replace("Bearer ", "")

        # Chame a função para criar o depósito e gerar o PIX
        pix_data = create_deposit(token, amount, description)

        # Adicione a transação ao banco de dados
        add_transaction(
            transaction_id=pix_data["transaction_id"],
            amount=amount,
            description=description,
            status="pending",
            qr_code_url=pix_data["pix_qr_code"],
            pix_code=pix_data["pix_key"]
        )

        return jsonify(pix_data), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
