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
    if response.status_code == 201:
        print('good')



# Tu modelo (Cliente)	EspoCRM (Lead)

# first_name	        firstName
# last_name	            lastName
# email	                emailAddress
# phone_number	        phoneNumber
# street	            addressStreet
# city	                addressCity
# state	                addressState
# postal_code	        addressPostalCode
# country	            addressCountry


# def register_user(cliente): 
#     user = User.objects.create(...) 
#     send_welcome_email(user.email) 
#     Analytics.track_event(user.id, "signup") 
#     Workspace.objects.create(user=user, name="My Workspace") 
#     return JsonResponse({"status": "ok"})