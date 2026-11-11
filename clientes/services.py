from .models import Cliente
import os
from dotenv import load_dotenv
import requests
import re
import json
from rest_framework.exceptions import APIException

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
    try:
        response = requests.post(espocrm_url, json=payload, headers=headers, timeout=10)
    except requests.exceptions.RequestException:
        raise APIException("No se pudo conectar con EspoCRM. Verifica que el servicio esté disponible.")

    return response

def check_repeated_char(word):
    patron = r"(.)\1{2,}"
    if word:
        return bool(re.search(patron, word))
    else:
        return False

def corregir_campos_con_ia(campos):
    """
    campos: dict {nombre_campo: valor} que necesitan corrección.
    Devuelve un dict con los valores corregidos, mismas llaves.
    """
    openrouter_url = os.getenv("openrouter_url")
    openrouter_api_key = os.getenv("openrouter_api_key")
    openrouter_model = os.getenv("openrouter_model")
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }
    campos_json = json.dumps(campos, ensure_ascii=False)
    prompt = f"""Recibirás un JSON con campos de texto que pueden tener errores de tecleo. Corrige cada valor aplicando SOLO estas reglas:

1. Si una letra está repetida de forma excesiva (3 o más veces seguidas) por error de tecleo, colapsa la repetición a la forma normal de la palabra. Ejemplo: "Valdezzzzzzzzzzzz" -> "Valdez".
2. Pon cada valor en formato Título: la primera letra de cada palabra en mayúscula, y TODAS las demás letras de esa palabra en minúscula, sin importar cómo estén escritas en el texto original. Ejemplo: "ValdeZZZZZZZZZZZZZzzz" -> "Valdez". "baja californiaaaaaaaaaa" -> "Baja California".
3. No agregues ni quites espacios que no sean parte de la corrección. No inventes información nueva.

Responde ÚNICAMENTE con un JSON válido con exactamente las mismas llaves que recibiste, sin explicaciones ni comentarios adicionales.

JSON a corregir:
{campos_json}"""

    payload = {
        "model": openrouter_model,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(openrouter_url, headers=headers, json=payload, timeout=15)
    except requests.exceptions.RequestException:
        raise APIException("No se pudo conectar con el servicio de IA. Intenta de nuevo en unos momentos.")
    data = response.json()
    contenido = data['choices'][0]['message']['content'].strip()

    if contenido.startswith("```"):
        contenido = contenido.split("```")[1]
        if contenido.startswith("json"):
            contenido = contenido[4:]
        contenido = contenido.strip()

    return json.loads(contenido)

def extraer_datos_con_ia(texto):
    openrouter_url = os.getenv("openrouter_url")
    openrouter_api_key = os.getenv("openrouter_api_key")
    openrouter_model = os.getenv("openrouter_model")

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""Extrae los siguientes datos de cliente del texto proporcionado y responde ÚNICAMENTE con un JSON válido, sin explicaciones ni texto adicional, usando exactamente estas llaves:

{{
    "first_name": "",
    "last_name": "",
    "email": "",
    "phone_number": "",
    "street": "",
    "city": "",
    "state": "",
    "postal_code": "",
    "country": ""
}}

Si algún dato no se encuentra en el texto, deja el valor como una cadena vacía "".

Texto a analizar:
{texto}"""

    payload = {
        "model": openrouter_model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(openrouter_url, headers=headers, json=payload, timeout=15)
    except requests.exceptions.RequestException:
        raise APIException("No se pudo conectar con el servicio de IA. Intenta de nuevo en unos momentos.")
    data = response.json()
    contenido = data['choices'][0]['message']['content'].strip()

    if contenido.startswith("```"):
        contenido = contenido.split("```")[1]
        if contenido.startswith("json"):
            contenido = contenido[4:]
        contenido = contenido.strip()

    datos_extraidos = json.loads(contenido)

    return datos_extraidos