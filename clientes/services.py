from .models import Cliente
import os
from dotenv import load_dotenv
import requests
import re

load_dotenv()

def mapear_cliente(cliente):
    payload = {
        "firstName": cliente.first_name,
        "lastName": cliente.last_name,
        "emailAddress": cliente.email,
        "phoneNumber": cliente.phone_number,
        "addressStreet": cliente.street,
        "addressPostalCode": cliente.postal_code,
        "addressCity": cliente.city,
        "addressState": cliente.state,
        "addressCountry": cliente.country
    }

    return payload

def enviar_cliente(payload):
    espocrm_url = os.getenv("espocrm_url")
    espocrm_api_key = os.getenv("espocrm_api_key")
    headers = {
        "x-api-key": espocrm_api_key,
    }
    response = requests.post(espocrm_url, json=payload, headers=headers)
    
    return response

def check_repeated_char(word):
    patron = r"(.)\1{2,}"
    if word:
        return bool(re.search(patron, word))
    else:
        return False

def corregir_texto_con_ia(texto):
    openrouter_url = os.getenv("openrouter_url")
    openrouter_api_key = os.getenv("openrouter_api_key")
    openrouter_model = os.getenv("openrouter_model")

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": openrouter_model,
        "messages": [
            {
                "role": "user",
                "content": f"Corrige este texto si tiene errores de tecleo o letras repetidas incorrectamente, como capitalización. Responde ÚNICAMENTE con el texto corregido, sin explicaciones ni comentarios adicionales: {texto}"
            }
        ]
    }

    response = requests.post(openrouter_url, headers=headers, json=payload)
    data = response.json()
    texto_corregido = data['choices'][0]['message']['content'].strip()

    return texto_corregido

