from rest_framework import viewsets
from .models import Cliente
from .serializers import ClienteSerializer
from .services import mapear_cliente, enviar_cliente, check_repeated_char, corregir_campos_con_ia, extraer_datos_con_ia
from django.db import transaction
from rest_framework.exceptions import APIException
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError


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
    total = clientes.count()
    enviados = clientes.filter(enviado_a_crm=True).count()
    con_correccion = clientes.filter(correccion_aplicada=True).count()

    stats = {
        "total": total,
        "enviados": enviados,
        "porcentaje_enviados": round((enviados / total * 100), 1) if total else 0,
        "con_correccion": con_correccion,
        "porcentaje_correccion": round((con_correccion / total * 100), 1) if total else 0,
    }

    return render(request, "clientes/listar_clientes.html", {"clientes": clientes, "stats": stats})

def captura_rapida(request):
    if request.method == "POST":
        texto = request.POST.get("texto_crudo")
        try:
            datos = extraer_datos_con_ia(texto)
            return render(request, "clientes/captura_cliente.html", {"datos": datos})
        except Exception as e:
            return render(request, "clientes/captura_rapida.html", {"error": str(e)})

    return render(request, "clientes/captura_rapida.html")