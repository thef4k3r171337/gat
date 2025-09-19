import os
from flask import Flask, jsonify, request
import secrets

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
            "POST /api/v1/test - Teste com autenticação"
        ]
    })

@app.route("/api/v1/test", methods=["POST"])
@require_api_key
def test_auth():
    return jsonify({
        "message": "Autenticação funcionando!",
        "authenticated": True
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/init-db")
def initialize_database():
    from database import init_db
    init_db()
    return jsonify({"message": "Database initialized successfully!"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
