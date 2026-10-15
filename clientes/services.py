from .models import Cliente
import os
from dotenv import load_dotenv
import requests

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
