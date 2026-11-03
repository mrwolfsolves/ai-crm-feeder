from rest_framework import viewsets
from .models import Cliente
from .serializers import ClienteSerializer
from .services import mapear_cliente, enviar_cliente, check_repeated_char, corregir_texto_con_ia
from django.db import transaction
from rest_framework.exceptions import APIException

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