  
# auth.py
import requests
import json

def authenticate(client_id, client_secret):
    url = "https://api.the-key.club/api/auth/login"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        return response.json()["token"]
    else:
        raise Exception(f"Falha na autenticação: {response.status_code} - {response.text}")
