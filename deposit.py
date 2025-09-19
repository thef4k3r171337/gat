import requests
import json
import base64
import qrcode
from io import BytesIO
import os

# URL Base da API the-key.club
BASE_API_URL = "https://api.the-key.club"

# Credenciais da API the-key.club (lidas de variáveis de ambiente )
CLIENT_ID = os.environ.get("THE_KEY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("THE_KEY_CLIENT_SECRET")

def get_jwt_token(client_id, client_secret):
    auth_url = f"{BASE_API_URL}/api/auth/login"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(auth_url, headers=headers, data=json.dumps(data))
    response.raise_for_status() # Levanta um erro para status de resposta HTTP ruins (4xx ou 5xx)
    return response.json()["token"]

def create_deposit(amount, description):
    try:
        # 1. Obter o token JWT
        jwt_token = get_jwt_token(CLIENT_ID, CLIENT_SECRET)

        # 2. Usar o token para criar o depósito
        deposit_url = f"{BASE_API_URL}/api/payments/deposit"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
        
        # URL de Callback (lida de variável de ambiente)
        data = {
            "amount": amount,
            "external_id": "id_unico_" + str(os.urandom(8).hex()),  # ID único para controle idempotente
            "clientCallbackUrl": os.environ.get("THE_KEY_CALLBACK_URL", "https://api-pix-service.onrender.com/callback" ),  # A URL de callback para receber notificações
            "payer": {
                "name": "João da Silva",  # Nome do pagador
                "email": "joao@example.com",  # Email do pagador
                "document": "12345678901"  # Documento do pagador
            },
            "description": description  # Descrição do depósito
        }
        
        response = requests.post(deposit_url, headers=headers, data=json.dumps(data))
        response.raise_for_status() # Levanta um erro para status de resposta HTTP ruins (4xx ou 5xx)
        deposit_data = response.json()
        
        if 'qrCodeResponse' in deposit_data and 'qrcode' in deposit_data['qrCodeResponse']:
            qr_code_data = deposit_data['qrCodeResponse']['qrcode']
            
            # Gerar QR Code localmente usando a biblioteca qrcode
            img = qrcode.make(qr_code_data)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                'pix_qr_code': f"data:image/png;base64,{qr_code_base64}",
                'pix_key': deposit_data['qrCodeResponse']['transactionId'], # Usando transactionId como pix_key
                'transaction_id': deposit_data['qrCodeResponse']['transactionId']
            }
        else:
            raise Exception("QR Code não encontrado na resposta da API.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição à API the-key.club: {e}")
        if e.response is not None:
            print(f"Resposta da API: {e.response.text}")
        raise Exception(f"Erro ao criar depósito: {e}")
    except Exception as e:
        raise Exception(f"Erro inesperado ao criar depósito: {e}")
