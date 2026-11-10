from rest_framework import viewsets
from .models import Cliente
from .serializers import ClienteSerializer
from .services import mapear_cliente, enviar_cliente, check_repeated_char, corregir_campos_con_ia, extraer_datos_con_ia
from django.db import transaction
from rest_framework.exceptions import APIException
from django.shortcuts import render, redirect


def capturar_cliente(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                cliente = Cliente.objects.create(
                    first_name=request.POST.get("first_name"),
                    last_name=request.POST.get("last_name"),
                    email=request.POST.get("email"),
                    phone_number=request.POST.get("phone_number"),
                    street=request.POST.get("street"),
                    city=request.POST.get("city"),
                    state=request.POST.get("state"),
                    postal_code=request.POST.get("postal_code"),
                    country=request.POST.get("country"),
                )

                campos_a_revisar = ["first_name", "last_name", "street", "city", "state"]
                campos_con_error = {
                    campo: getattr(cliente, campo)
                    for campo in campos_a_revisar
                    if check_repeated_char(getattr(cliente, campo))
                }
                if campos_con_error:
                    corregidos = corregir_campos_con_ia(campos_con_error)
                    for campo, valor in corregidos.items():
                        setattr(cliente, campo, valor)
                cliente.save()
                

                cliente_mapeado = mapear_cliente(cliente)
                response = enviar_cliente(cliente_mapeado)

                if response.status_code == 409:
                    raise APIException("Ya existe un cliente con estos datos (nombre o correo) registrado en el CRM.")
                elif response.status_code != 200:
                    raise APIException("No se pudo enviar el cliente a EspoCRM")

            return render(request, "clientes/captura_cliente.html", {"exito": True})
        except Exception as e:
            return render(request, "clientes/captura_cliente.html", {"error": str(e)})

    return render(request, "clientes/captura_cliente.html")

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()
        cliente = serializer.instance

        campos_a_revisar = ["first_name", "last_name", "street", "city", "state"]
        campos_con_error = {
            campo: getattr(cliente, campo)
            for campo in campos_a_revisar
            if check_repeated_char(getattr(cliente, campo))
        }
        if campos_con_error:
            corregidos = corregir_campos_con_ia(campos_con_error)
            for campo, valor in corregidos.items():
                setattr(cliente, campo, valor)
        cliente.save()
        

        cliente_mapeado = mapear_cliente(cliente)
        response = enviar_cliente(cliente_mapeado)

        if response.status_code == 409:
            raise APIException("Ya existe un cliente con estos datos (nombre o correo) registrado en el CRM.")
        elif response.status_code != 200:
            raise APIException("No se pudo enviar el cliente a EspoCRM")

def listar_clientes(request):
    clientes = Cliente.objects.all().order_by("-created_at")
    return render(request, "clientes/listar_clientes.html", {"clientes": clientes})

def captura_rapida(request):
    if request.method == "POST":
        texto = request.POST.get("texto_crudo")
        datos = extraer_datos_con_ia(texto)
        return render(request, "clientes/captura_cliente.html", {"datos": datos})

    return render(request, "clientes/captura_rapida.html")