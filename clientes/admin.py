from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "first_name", "last_name", "email", "city", "state",
        "enviado_a_crm", "correccion_aplicada", "created_at",
    )
    list_filter = ("enviado_a_crm", "correccion_aplicada", "city", "state")
    search_fields = ("first_name", "last_name", "email", "phone_number")
    readonly_fields = ("created_at", "valores_originales")