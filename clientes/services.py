from .models import Cliente
import os
from dotenv import load_dotenv
import requests
import re
import json
from rest_framework.exceptions import APIException
import logging
import io
from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger("clientes")

load_dotenv()

def mapear_cliente(cliente):
    descripcion = "\n".join(filter(None, [
        f"Productos de interés: {cliente.products_of_interest}" if cliente.products_of_interest else "",
        f"Observaciones: {cliente.notes}" if cliente.notes else "",
    ]))

    payload = {
        "firstName": cliente.first_name,
        "lastName": cliente.last_name,
        "emailAddress": cliente.email,
        "phoneNumber": normalizar_telefono(cliente.phone_number),
        "addressStreet": cliente.street,
        "addressPostalCode": cliente.postal_code,
        "addressCity": cliente.city,
        "addressState": cliente.state,
        "addressCountry": cliente.country,
        "accountName": cliente.company,
        "title": cliente.position,
        "description": descripcion,
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
        logger.error(f"No se pudo conectar con EspoCRM para el cliente {payload.get('emailAddress')}")
        raise APIException("No se pudo conectar con EspoCRM. Verifica que el servicio esté disponible.")

    if response.status_code == 200:
        logger.info(f"Cliente enviado a EspoCRM correctamente: {payload.get('emailAddress')}")
    else:
        logger.warning(f"EspoCRM respondió {response.status_code} para el cliente {payload.get('emailAddress')}: {response.text}")

    return response

def tiene_anomalia(texto):
    """
    Detecta si un campo de texto tiene un posible error de tecleo:
    letras repetidas en exceso, o caracteres que no deberían estar
    en un nombre/dirección (símbolos, signos sueltos, etc.).
    """
    if not texto:
        return False
    patron_repetidos = r"(.)\1{2,}"
    patron_caracteres_invalidos = r"[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']"
    return bool(re.search(patron_repetidos, texto)) or bool(re.search(patron_caracteres_invalidos, texto))

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
2. Si hay símbolos o caracteres que claramente no deberían estar ahí (ej. "Mart[inez"), corrígelos para formar la palabra correcta más probable según el contexto (nombres, apellidos, ciudades o estados reales). Ejemplo: "Mart[inez" -> "Martínez".
3. Pon cada valor en formato Título: la primera letra de cada palabra en mayúscula, y TODAS las demás letras de esa palabra en minúscula, sin importar cómo estén escritas en el texto original. Ejemplo: "ValdeZZZZZZZZZZZZZzzz" -> "Valdez". "baja californiaaaaaaaaaa" -> "Baja California".
4. No agregues ni quites espacios que no sean parte de la corrección. No inventes información nueva.

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

    if "choices" not in data:
        logger.error(f"Respuesta inesperada de OpenRouter: {data}")
        raise APIException("El servicio de IA no respondió correctamente. Verifica la configuración o intenta más tarde.")

    contenido = data['choices'][0]['message']['content'].strip()

    if contenido.startswith("```"):
        contenido = contenido.split("```")[1]
        if contenido.startswith("json"):
            contenido = contenido[4:]
        contenido = contenido.strip()

    try:
        resultado = json.loads(contenido)
    except json.JSONDecodeError:
        logger.error(f"La IA regresó un JSON inválido al corregir campos: {contenido}")
        raise APIException("La IA no pudo procesar la corrección, intenta de nuevo.")
    logger.info(f"Corrección IA aplicada a campos: {list(campos.keys())}")
    return resultado

def extraer_datos_con_ia(texto):
    openrouter_url = os.getenv("openrouter_url")
    openrouter_api_key = os.getenv("openrouter_api_key")
    openrouter_model = os.getenv("openrouter_model")

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""Extrae los datos de UN SOLO cliente del texto proporcionado y responde ÚNICAMENTE con un JSON válido, sin explicaciones ni texto adicional, usando exactamente estas llaves:

{{
    "first_name": "",
    "last_name": "",
    "email": "",
    "phone_number": "",
    "street": "",
    "city": "",
    "state": "",
    "postal_code": "",
    "country": "",
    "company": "",
    "position": "",
    "products_of_interest": "",
    "notes": ""
}}

Reglas:
1. Si algún dato no se encuentra en el texto, deja el valor como una cadena vacía "". No inventes información.
2. Si el nombre completo tiene varias palabras (ej. "Juan Pérez García"), usa la primera palabra como first_name y el resto como last_name.
3. Si el texto menciona a más de un cliente, extrae SOLO los datos del primero que aparezca.
4. El texto puede estar en español o en inglés; extrae los datos sin importar el idioma.
5. "company" es el nombre de la empresa u organización del cliente, si se menciona.
6. "position" es el cargo o puesto del cliente dentro de su empresa (ej. "Gerente de compras", "Director de TI").
7. "products_of_interest" son los productos, servicios o soluciones que el cliente menciona que le interesan o está buscando.
8. "notes" son observaciones generales relevantes que no encajen en los demás campos (ej. "urge cotización para esta semana").

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

    if "choices" not in data:
        logger.error(f"Respuesta inesperada de OpenRouter: {data}")
        raise APIException("El servicio de IA no respondió correctamente. Verifica la configuración o intenta más tarde.")

    contenido = data['choices'][0]['message']['content'].strip()

    if contenido.startswith("```"):
        contenido = contenido.split("```")[1]
        if contenido.startswith("json"):
            contenido = contenido[4:]
        contenido = contenido.strip()

    try:
        datos_extraidos = json.loads(contenido)
    except json.JSONDecodeError:
        logger.error(f"La IA regresó un JSON inválido al extraer datos: {contenido}")
        raise APIException("La IA no pudo extraer los datos del texto, intenta reformularlo o inténtalo de nuevo.")

    LLAVES_ESPERADAS = {
        "first_name", "last_name", "email", "phone_number",
        "street", "city", "state", "postal_code", "country",
        "company", "position", "products_of_interest", "notes",
    }

    if not isinstance(datos_extraidos, dict) or set(datos_extraidos.keys()) != LLAVES_ESPERADAS:
        logger.error(f"La IA regresó llaves inesperadas al extraer datos: {datos_extraidos}")
        raise APIException("La IA no pudo extraer los datos correctamente, intenta reformular el texto.")

    return datos_extraidos

def extraer_texto_de_pdf(archivo):
    """
    archivo: un InMemoryUploadedFile (request.FILES) o similar con método .read()
    Devuelve el texto plano extraído de todas las páginas del PDF.
    """
    try:
        lector = PdfReader(io.BytesIO(archivo.read()))
    except PdfReadError:
        raise APIException("El archivo no es un PDF válido o está dañado.")

    texto = ""
    for pagina in lector.pages:
        texto += pagina.extract_text() or ""

    if not texto.strip():
        raise APIException("No se pudo extraer texto del PDF. Es posible que sea un documento escaneado (imagen) sin texto seleccionable.")

    return texto

def normalizar_telefono(numero, codigo_pais_default="52"):
    """
    Normaliza un número telefónico a formato internacional E.164 (+52...).
    Si el número ya trae un '+', se asume que el usuario ya puso el código de país.
    """
    if not numero:
        return numero

    numero = numero.strip()
    if numero.startswith("+"):
        return numero

    solo_digitos = re.sub(r"\D", "", numero)
    return f"+{codigo_pais_default}{solo_digitos}"