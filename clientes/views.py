from rest_framework import viewsets
from .models import Cliente
from .serializers import ClienteSerializer
from .services import mapear_cliente, enviar_cliente, check_repeated_char, corregir_texto_con_ia
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

                if check_repeated_char(cliente.first_name):
                    cliente.first_name = corregir_texto_con_ia(cliente.first_name)
                if check_repeated_char(cliente.last_name):
                    cliente.last_name = corregir_texto_con_ia(cliente.last_name)
                cliente.save()

                cliente_mapeado = mapear_cliente(cliente)
                response = enviar_cliente(cliente_mapeado)

                if response.status_code != 200:
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

        if check_repeated_char(cliente.first_name):
            cliente.first_name = corregir_texto_con_ia(cliente.first_name)
        if check_repeated_char(cliente.last_name):
            cliente.last_name = corregir_texto_con_ia(cliente.last_name)
        cliente.save()

        cliente_mapeado = mapear_cliente(cliente)
        response = enviar_cliente(cliente_mapeado)

        if response.status_code != 200:
            raise APIException("No se pudo enviar el cliente a EspoCRM")