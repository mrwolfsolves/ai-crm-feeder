from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, capturar_cliente, listar_clientes, captura_rapida, detalle_cliente, exportar_clientes_csv
from django.urls import path

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)

urlpatterns = router.urls + [
    path("capturar/", capturar_cliente, name="capturar_cliente"),
    path("listar/", listar_clientes, name="listar_clientes"),
    path("captura-rapida/", captura_rapida, name="captura_rapida"),
    path("clientes/<int:pk>/detalle/", detalle_cliente, name="detalle_cliente"),
    path("exportar-clientes/", exportar_clientes_csv, name="exportar_clientes_csv"),
]