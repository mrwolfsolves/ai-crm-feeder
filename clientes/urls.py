from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, capturar_cliente
from django.urls import path

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)

urlpatterns = router.urls + [
    path("capturar/", capturar_cliente, name="capturar_cliente"),
]