def mapear_cliente(cliente):
    "first_name":firstName



def register_user(cliente): 
    user = User.objects.create(...) 
    send_welcome_email(user.email) 
    Analytics.track_event(user.id, "signup") 
    Workspace.objects.create(user=user, name="My Workspace") 
    return JsonResponse({"status": "ok"})