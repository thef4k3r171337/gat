from flask import Flask, render_template, request, jsonify
from auth import authenticate
from deposit import create_deposit
from database import init_db, add_transaction, update_transaction_status, get_transaction
from functools import wraps
import sqlite3
from datetime import datetime
import requests

app = Flask(__name__)

# Seu Client ID e Secret
client_id = "iagohotpay(hot)_6656FA84"
client_secret = "4df7c31cad3efc3edadb61eeba0b79fb6bc4c2eef93c11d6e0860589c8fb1315c9cec04d52e633e6b9f9f38f25f2e89f9bc0"

# Função de autenticação
token = authenticate(client_id, client_secret)

# Inicializa o banco de dados
init_db()

# Inicializar tabelas da API
def init_api_tables():
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    
    # Tabela para chaves de API
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id TEXT UNIQUE NOT NULL,
            secret_key TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela para webhooks dos clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            webhook_url TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            delivered BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar tabelas da API
init_api_tables()

# Middleware de autenticação para API
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'API key required'}), 401
        
        api_key = auth_header.replace('Bearer ', '')
        
        # Validar a chave no banco
        conn = sqlite3.connect('transactions.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE secret_key = ? AND active = 1", (api_key,))
        key_data = cursor.fetchone()
        conn.close()
        
        if not key_data:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# ============= ROTAS ORIGINAIS (MANTIDAS) =============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_deposit', methods=['POST'])
def create_deposit_route():
    try:
        # Receber os dados JSON enviados pelo frontend
        data = request.get_json()
        amount = data.get('amount')
        description = data.get('description')
        
        print(f"Dados recebidos: {data}")  # Log para depuração

        if not amount or not description:
            return jsonify({'message': 'Dados inválidos ou ausentes!'}), 400

        # Chama a função para criar o depósito
        deposit_data = create_deposit(token, amount, description)
        
        # Adiciona a transação ao banco de dados com status PENDENTE
        add_transaction(deposit_data["transaction_id"], amount, description, 'PENDENTE', deposit_data['pix_qr_code'], deposit_data['pix_key'])
        
        # Retorna os dados da resposta de forma JSON
        return jsonify({
            'qr_code_url': deposit_data['pix_qr_code'],
            'pix_code': deposit_data['pix_key'],
            'transaction_id': deposit_data['transaction_id']
        }), 200  # Retorna um código 200 (OK)
    
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'message': 'Erro ao criar o depósito!'}), 500

@app.route('/payment_status/<transaction_id>', methods=['GET'])
def payment_status(transaction_id):
    try:
        # Verifica o status da transação no banco de dados
        transaction = get_transaction(transaction_id)
        if transaction:
            status = transaction["status"]
            amount = transaction["amount"]
            return jsonify({"transaction_id": transaction_id, "status": status, "amount": amount}), 200
        else:
            return jsonify({'message': 'Transação não encontrada'}), 404

    except Exception as e:
        print(f"Erro ao verificar status: {e}")
        return jsonify({'message': 'Erro ao verificar o status da transação'}), 500

@app.route('/callback', methods=['POST'])
def callback():
    try:
        # Receber os dados do webhook
        data = request.json
        
        print(f"Callback recebido: {data}")
        
        # Processa a transação
        transaction_id = data['transaction_id']
        status = data['status']
        
        # Lógica para atualizar o status da transação no banco de dados
        if status == 'COMPLETED':
            # Alterando o status para 'PAGO' quando o pagamento for confirmado
            update_transaction_status(transaction_id, 'PAGO')
            print(f"Status da transação {transaction_id} alterado para PAGO!")
            
            # NOVA FUNCIONALIDADE: Notificar clientes via webhook
            notify_client_webhook(transaction_id, 'paid')
        
        # Enviar confirmação de que o callback foi recebido com sucesso
        return jsonify({"message": "Callback recebido com sucesso!"}), 200
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"message": "Erro ao processar o webhook"}), 500

# ============= NOVAS ROTAS DA API =============

@app.route('/api/v1/charges', methods=['POST'])
@require_api_key
def api_create_charge():
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('amount') or not data.get('description'):
            return jsonify({'error': 'amount and description are required'}), 400
        
        # Converter centavos para reais (se o valor for maior que 100, assume que está em centavos)
        amount_in_reais = data['amount'] / 100 if data['amount'] > 100 else data['amount']
        
        # Chamar sua função existente (sem modificar nada!)
        deposit_data = create_deposit(token, amount_in_reais, data['description'])
        
        # Salvar no banco (usando sua função existente)
        add_transaction(
            deposit_data["transaction_id"], 
            amount_in_reais, 
            data['description'], 
            'PENDENTE', 
            deposit_data['pix_qr_code'], 
            deposit_data['pix_key']
        )
        
        # Se o cliente forneceu uma URL de webhook, salvar
        if data.get('notification_url'):
            save_client_webhook(deposit_data["transaction_id"], data['notification_url'])
        
        # Responder no formato da API
        return jsonify({
            'id': deposit_data['transaction_id'],
            'status': 'pending',
            'amount': data['amount'],
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'pix_qr_code': deposit_data['pix_qr_code'],
            'pix_copy_paste': deposit_data['pix_key']
        }), 201
        
    except Exception as e:
        print(f"Erro na API create_charge: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/charges/<transaction_id>', methods=['GET'])
@require_api_key
def api_get_charge(transaction_id):
    try:
        # Usar sua função existente
        transaction = get_transaction(transaction_id)
        
        if not transaction:
            return jsonify({'error': 'Charge not found'}), 404
        
        # Traduzir status interno para status da API
        api_status = 'paid' if transaction['status'] == 'PAGO' else 'pending'
        
        return jsonify({
            'id': transaction['transaction_id'],
            'status': api_status,
            'amount': int(transaction['amount'] * 100),  # Converter para centavos
            'description': transaction['description'],
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        print(f"Erro na API get_charge: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============= FUNÇÕES AUXILIARES DA API =============

def save_client_webhook(transaction_id, webhook_url):
    """Salva a URL de webhook do cliente para uma transação"""
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO client_webhooks (transaction_id, webhook_url) VALUES (?, ?)",
        (transaction_id, webhook_url)
    )
    conn.commit()
    conn.close()

def notify_client_webhook(transaction_id, status):
    """Notifica o cliente via webhook quando o status da transação muda"""
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT webhook_url FROM client_webhooks WHERE transaction_id = ? AND delivered = 0",
        (transaction_id,)
    )
    webhook_data = cursor.fetchone()
    
    if webhook_data:
        webhook_url = webhook_data[0]
        payload = {
            'event_type': 'charge.paid',
            'data': {
                'id': transaction_id,
                'status': status,
                'paid_at': datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                # Marcar como entregue
                cursor.execute(
                    "UPDATE client_webhooks SET delivered = 1, attempts = attempts + 1 WHERE transaction_id = ?",
                    (transaction_id,)
                )
                conn.commit()
                print(f"Webhook enviado com sucesso para {webhook_url}")
            else:
                # Incrementar tentativas
                cursor.execute(
                    "UPDATE client_webhooks SET attempts = attempts + 1 WHERE transaction_id = ?",
                    (transaction_id,)
                )
                conn.commit()
                print(f"Erro no webhook: HTTP {response.status_code}")
        except Exception as e:
            # Incrementar tentativas
            cursor.execute(
                "UPDATE client_webhooks SET attempts = attempts + 1 WHERE transaction_id = ?",
                (transaction_id,)
            )
            conn.commit()
            print(f"Erro ao enviar webhook: {e}")
    
    conn.close()

# ============= ROTAS ADMINISTRATIVAS =============

@app.route('/admin/create_api_key', methods=['POST'])
def create_api_key():
    """Rota para criar chaves de API (você pode proteger isso depois)"""
    try:
        data = request.get_json()
        client_name = data.get('client_name')
        
        if not client_name:
            return jsonify({'error': 'client_name is required'}), 400
        
        # Gerar chaves
        import secrets
        key_id = f"pk_live_{secrets.token_urlsafe(16)}"
        secret_key = f"sk_live_{secrets.token_urlsafe(32)}"
        
        # Salvar no banco
        conn = sqlite3.connect('transactions.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_keys (key_id, secret_key, client_name) VALUES (?, ?, ?)",
            (key_id, secret_key, client_name)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'key_id': key_id,
            'secret_key': secret_key,
            'client_name': client_name
        }), 201
        
    except Exception as e:
        print(f"Erro ao criar API key: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)
