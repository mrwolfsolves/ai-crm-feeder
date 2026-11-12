from django.test import TestCase
from unittest.mock import patch, Mock
from .models import Cliente
from .services import tiene_anomalia, mapear_cliente, corregir_campos_con_ia, extraer_datos_con_ia

class TieneAnomaliaTests(TestCase):
    def test_detecta_tres_o_mas_repeticiones(self):
        self.assertTrue(tiene_anomalia("Valdezzzzzzzzzzzz"))
        self.assertTrue(tiene_anomalia("tijuanaaaaaaa"))

    def test_detecta_caracteres_invalidos(self):
        self.assertTrue(tiene_anomalia("Mart[inez"))
        self.assertTrue(tiene_anomalia("Juan#Perez"))

    def test_no_detecta_repeticiones_normales(self):
        self.assertFalse(tiene_anomalia("Pizza"))
        self.assertFalse(tiene_anomalia("Valdez"))
        self.assertFalse(tiene_anomalia("Tijuana"))

    def test_texto_vacio_o_none(self):
        self.assertFalse(tiene_anomalia(""))
        self.assertFalse(tiene_anomalia(None))

    def test_dos_repeticiones_no_cuentan(self):
        self.assertFalse(tiene_anomalia("correo"))
        self.assertFalse(tiene_anomalia("carro"))

    def test_acepta_guiones_y_apostrofes(self):
        self.assertFalse(tiene_anomalia("Jean-Pierre"))
        self.assertFalse(tiene_anomalia("O'Brien"))


class MapearClienteTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            first_name="Leonardo",
            last_name="Valdez",
            email="leo@example.com",
            phone_number="+526648468786",
            street="Calle Reforma",
            city="Tijuana",
            state="Baja California",
            postal_code="22205",
            country="México",
        )

    def test_mapeo_correcto_a_formato_espocrm(self):
        payload = mapear_cliente(self.cliente)
        self.assertEqual(payload["firstName"], "Leonardo")
        self.assertEqual(payload["lastName"], "Valdez")
        self.assertEqual(payload["emailAddress"], "leo@example.com")
        self.assertEqual(payload["phoneNumber"], "+526648468786")
        self.assertEqual(payload["addressStreet"], "Calle Reforma")
        self.assertEqual(payload["addressCity"], "Tijuana")
        self.assertEqual(payload["addressState"], "Baja California")
        self.assertEqual(payload["addressPostalCode"], "22205")
        self.assertEqual(payload["addressCountry"], "México")

    def test_payload_tiene_exactamente_las_llaves_esperadas(self):
        payload = mapear_cliente(self.cliente)
        llaves_esperadas = {
            "firstName", "lastName", "emailAddress", "phoneNumber",
            "addressStreet", "addressPostalCode", "addressCity",
            "addressState", "addressCountry"
        }
        self.assertEqual(set(payload.keys()), llaves_esperadas)

class CorregirCamposConIATests(TestCase):
    @patch("clientes.services.requests.post")
    def test_corrige_campos_correctamente(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"last_name": "Valdez"}'}}
            ]
        }
        mock_post.return_value = mock_response

        resultado = corregir_campos_con_ia({"last_name": "Valdezzzzzzzzzzzz"})

        self.assertEqual(resultado, {"last_name": "Valdez"})
        mock_post.assert_called_once()

    @patch("clientes.services.requests.post")
    def test_maneja_respuesta_envuelta_en_markdown(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '```json\n{"city": "Tijuana"}\n```'}}
            ]
        }
        mock_post.return_value = mock_response

        resultado = corregir_campos_con_ia({"city": "tijuanaaaaaa"})

        self.assertEqual(resultado, {"city": "Tijuana"})


class ExtraerDatosConIATests(TestCase):
    @patch("clientes.services.requests.post")
    def test_extrae_datos_correctamente(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"first_name": "Leonardo", "last_name": "Valdez", "email": "", "phone_number": "", "street": "", "city": "", "state": "", "postal_code": "", "country": ""}'}}
            ]
        }
        mock_post.return_value = mock_response

        resultado = extraer_datos_con_ia("Me llamo Leonardo Valdez")

        self.assertEqual(resultado["first_name"], "Leonardo")
        self.assertEqual(resultado["last_name"], "Valdez")