# Alimentador de CRM con IA (CRM Feeder)

Sistema web que automatiza la captura de datos de clientes en el CRM de Digiproduct (EspoCRM), sustituyendo el proceso manual de captura. Usa un modelo de lenguaje para detectar y corregir inconsistencias en los datos capturados, y para extraer datos estructurados a partir de texto libre.

## Stack

- Django + Django REST Framework
- MySQL (SQLite en desarrollo local)
- EspoCRM (API REST, vía Docker en entorno de desarrollo)
- OpenRouter (API de IA, modelo configurable)
- Bootstrap 5

## Funcionalidades

- Captura de clientes vía formulario web, con corrección automática de errores de tecleo (letras repetidas, capitalización) antes de enviarlos al CRM.
- Captura rápida: pega un texto libre (ej. un correo o mensaje de un cliente) y la IA extrae los datos estructurados automáticamente.
- Envío automático de los clientes capturados a EspoCRM vía su API REST.
- Manejo de conflictos de duplicados (409) del CRM con mensajes claros para el usuario.
- API REST propia (Django REST Framework) para consultar/crear/modificar clientes.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/GaliDaVinci/ai-crm-feeder.git
   cd ai-crm-feeder
   ```

2. Crea el entorno virtual e instala dependencias (usando `uv`):
   ```bash
   uv venv
   source .venv/bin/activate   # En Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```
   espocrm_url=http://localhost:8080/api/v1/Lead
   espocrm_api_key=tu_api_key_de_espocrm
   openrouter_url=https://openrouter.ai/api/v1/chat/completions
   openrouter_api_key=tu_api_key_de_openrouter
   openrouter_model=nombre-del-modelo
   ```

4. Aplica las migraciones:
   ```bash
   python manage.py migrate
   ```

5. Corre el servidor:
   ```bash
   python manage.py runserver
   ```

## EspoCRM (entorno de desarrollo)

Para pruebas locales, EspoCRM se levanta vía Docker (ver `docker-compose.yml` en `espocrm-docker/`):

```bash
cd espocrm-docker
docker compose up -d
```

El panel queda disponible en `http://localhost:8080`.

## Rutas principales

- `/capturar/` — formulario de captura de cliente
- `/captura-rapida/` — captura de cliente a partir de texto libre (extracción con IA)
- `/listar/` — listado de clientes capturados
- `/clientes/` — API REST (DRF)

## Contexto

Proyecto desarrollado como parte de las estadías profesionales de Leonardo Valdez en Digiproduct, para la carrera de Ingeniería en Tecnologías de la Información (área DSM) en la UTT.