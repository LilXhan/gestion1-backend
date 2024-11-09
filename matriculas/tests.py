from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from .serializers import EstudianteSerializer
from .models import Estudiante
from django.contrib.auth.models import User

class MatriculaSistemaTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.registro_url = reverse("registro")
        self.login_url = reverse("login")
        self.matricula_url = reverse("matricula")
        self.pago_url = reverse("pago")

    def test_proceso_completo_registro_matricula_y_pago(self):
        # Registrar usuario
        response = self.client.post(self.registro_url, {
            "username": "testuser",
            "password": "12345",
            "email": "testuser@example.com"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Login
        response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "12345"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data["token"]

        # Agregar token a las credenciales del cliente
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)

        # Realizar matrícula
        response = self.client.post(self.matricula_url, {
            "curso_id": 1,
            "año_escolar": "2024"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Realizar pago
        response = self.client.post(self.pago_url, {
            "monto": 100.0,
            "metodo": "stripe"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class RegistroMatriculaIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.registro_url = reverse("registro")
        self.matricula_url = reverse("matricula")

    def test_registro_y_matricula(self):
        # Registrar un usuario
        response = self.client.post(self.registro_url, {
            "username": "testuser",
            "password": "12345",
            "email": "testuser@example.com"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Iniciar sesión para obtener el token
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "12345"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data["token"]
        
        # Realizar matrícula con el token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.post(self.matricula_url, {
            "curso_id": 1,  # Supongamos que existe un curso con ID 1
            "año_escolar": "2024"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class EstudianteSerializerTestCase(TestCase):
    def test_estudiante_serializer(self):
        estudiante = Estudiante.objects.create(nombre="Juan", edad=15)
        serializer = EstudianteSerializer(estudiante)
        expected_data = {
            "id": estudiante.id,
            "nombre": "Juan",
            "edad": 15
        }
        self.assertEqual(serializer.data, expected_data)

class UserModelTestCase(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username="testuser", password="12345")
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "testuser")