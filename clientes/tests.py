from django.test import TestCase
from .models import Cliente
from .services import check_repeated_char, mapear_cliente


class CheckRepeatedCharTests(TestCase):
    def test_detecta_tres_o_mas_repeticiones(self):
        self.assertTrue(check_repeated_char("Valdezzzzzzzzzzzz"))
        self.assertTrue(check_repeated_char("tijuanaaaaaaa"))

    def test_no_detecta_repeticiones_normales(self):
        self.assertFalse(check_repeated_char("Pizza"))
        self.assertFalse(check_repeated_char("Valdez"))
        self.assertFalse(check_repeated_char("Tijuana"))

    def test_texto_vacio_o_none(self):
        self.assertFalse(check_repeated_char(""))
        self.assertFalse(check_repeated_char(None))

    def test_dos_repeticiones_no_cuentan(self):
        # el patrón exige 3+, dos letras iguales seguidas no deben marcarse
        self.assertFalse(check_repeated_char("correo"))
        self.assertFalse(check_repeated_char("carro"))


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