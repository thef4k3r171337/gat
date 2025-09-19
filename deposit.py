
import requests
import json
import base64
import qrcode
from io import BytesIO

def create_deposit(token, amount, description):
    url = "https://api.the-key.club/api/payments/deposit"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # URL de Callback (pode ser ajustada conforme necessário )
    data = {
        "amount": amount,
        "external_id": "id_unico_12345",  # ID único para controle idempotente
        "clientCallbackUrl": "https://api-pix-service.onrender.com/callback",  # A URL de callback para receber notificações
        "payer": {
            "name": "João da Silva",  # Nome do pagador
            "email": "joao@example.com",  # Email do pagador
            "document": "12345678901"  # Documento do pagador
        },
        "description": description  # Descrição do depósito
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data ))
    
    if response.status_code == 201:
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
                'pix_key': deposit_data['qrCodeResponse']['transactionId'],
                'transaction_id': deposit_data['qrCodeResponse']['transactionId']
            }
        else:
            raise Exception("QR Code não encontrado na resposta da API.")
    else:
        raise Exception(f"Erro ao criar depósito: {response.status_code} - {response.text}")
