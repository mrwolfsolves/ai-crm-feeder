from rest_framework import viewsets
from .models import Cliente
from .serializers import ClienteSerializer
from .services import mapear_cliente, enviar_cliente
from django.db import transaction

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()
        cliente = serializer.instance
        cliente_mapeado = mapear_cliente(cliente)
        response = enviar_cliente(cliente_mapeado)