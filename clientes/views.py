from rest_framework import viewsets
from .models import Cliente
from .serializers import ClienteSerializer
from .services import mapear_cliente, enviar_cliente, tiene_anomalia, corregir_campos_con_ia, extraer_datos_con_ia
from django.db import transaction
from rest_framework.exceptions import APIException
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Q


def capturar_cliente(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                cliente = Cliente(
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
                cliente.full_clean()
                cliente.save()

                campos_a_revisar = ["first_name", "last_name", "street", "city", "state"]
                campos_con_error = {
                    campo: getattr(cliente, campo)
                    for campo in campos_a_revisar
                    if tiene_anomalia(getattr(cliente, campo))
                }
                if campos_con_error:
                    cliente.valores_originales = campos_con_error
                    cliente.correccion_aplicada = True
                    corregidos = corregir_campos_con_ia(campos_con_error)
                    for campo, valor in corregidos.items():
                        setattr(cliente, campo, valor)
                

                cliente_mapeado = mapear_cliente(cliente)
                response = enviar_cliente(cliente_mapeado)

                if response.status_code == 409:
                    raise APIException("Ya existe un cliente con estos datos (nombre o correo) registrado en el CRM.")
                elif response.status_code != 200:
                    raise APIException("No se pudo enviar el cliente a EspoCRM")

                cliente.enviado_a_crm = True
                cliente.save()

            return render(request, "clientes/captura_cliente.html", {"exito": True})
        except ValidationError as e:
            errores = "; ".join(
                f"{campo}: {', '.join(mensajes)}" for campo, mensajes in e.message_dict.items()
            )
            return render(request, "clientes/captura_cliente.html", {"error": errores})
        except Exception as e:
            return render(request, "clientes/captura_cliente.html", {"error": str(e)})

    return render(request, "clientes/captura_cliente.html")

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filterset_fields = ["city", "state", "enviado_a_crm", "correccion_aplicada"]
    search_fields = ["first_name", "last_name", "email", "phone_number"]
    ordering_fields = ["created_at", "first_name", "last_name"]

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
            cliente.valores_originales = campos_con_error
            cliente.correccion_aplicada = True
            corregidos = corregir_campos_con_ia(campos_con_error)
            for campo, valor in corregidos.items():
                setattr(cliente, campo, valor)
        

        cliente_mapeado = mapear_cliente(cliente)
        response = enviar_cliente(cliente_mapeado)

        if response.status_code == 409:
            raise APIException("Ya existe un cliente con estos datos (nombre o correo) registrado en el CRM.")
        elif response.status_code != 200:
            raise APIException("No se pudo enviar el cliente a EspoCRM")

        cliente.enviado_a_crm = True
        cliente.save()

def listar_clientes(request):
    clientes = Cliente.objects.all().order_by("-created_at")

    query = request.GET.get("q", "").strip()
    if query:
        clientes = clientes.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    total = Cliente.objects.count()
    enviados = Cliente.objects.filter(enviado_a_crm=True).count()
    con_correccion = Cliente.objects.filter(correccion_aplicada=True).count()

    stats = {
        "total": total,
        "enviados": enviados,
        "porcentaje_enviados": round((enviados / total * 100), 1) if total else 0,
        "con_correccion": con_correccion,
        "porcentaje_correccion": round((con_correccion / total * 100), 1) if total else 0,
    }

    return render(request, "clientes/listar_clientes.html", {"clientes": clientes, "stats": stats, "query": query})

def captura_rapida(request):
    if request.method == "POST":
        texto = request.POST.get("texto_crudo")
        try:
            datos = extraer_datos_con_ia(texto)
            return render(request, "clientes/captura_cliente.html", {"datos": datos})
        except Exception as e:
            return render(request, "clientes/captura_rapida.html", {"error": str(e)})

    return render(request, "clientes/captura_rapida.html")

def detalle_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, "clientes/detalle_cliente.html", {"cliente": cliente})