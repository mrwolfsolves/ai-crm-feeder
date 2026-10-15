from .models import Cliente

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