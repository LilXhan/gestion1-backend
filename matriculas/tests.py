from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from matriculas.models import Estudiante, Matricula, Pago
from django.urls import reverse
from unittest.mock import patch

class VerificarEstudianteAPIViewTest(APITestCase):

    def setUp(self):
        # Crear un usuario y un estudiante asociado
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.estudiante = Estudiante.objects.create(
            usuario=self.user,
            nombre="Test Estudiante",
            dni="12345678",
            fecha_nacimiento="2000-01-01",
            grado="Grado 1",
            direccion="Direccion 1"
        )
        self.matricula = Matricula.objects.create(
            estudiante=self.estudiante,
            curso="Curso Ejemplo",
            monto=100.00
        )
        self.pago = Pago.objects.create(
            matricula=self.matricula,
            estado="Pendiente",
            stripe_payment_intent_id="pi_test_123"
        )
        self.url = reverse('verificar_estudiante')  # URL de la vista a probar

        # Obtener el token JWT para el usuario
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.token = response.data['access']

    @patch('stripe.PaymentIntent.retrieve')
    def test_verificar_estudiante_con_pago_pendiente(self, mock_retrieve):
        mock_retrieve.return_value = {'client_secret': 'test_secret'}

        # Hacer la solicitud GET con el token de autenticación en el encabezado
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer ' + self.token)

        # Comprobar que la respuesta es correcta y contiene los datos esperados
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])
        self.assertIn('client_secret', response.data)

    def test_verificar_estudiante_sin_pago(self):
        # Crear un pago completado
        self.pago.estado = "Completado"
        self.pago.save()

        # Hacer la solicitud GET con el token de autenticación en el encabezado
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer ' + self.token)

        # Comprobar que la respuesta es correcta y contiene los datos esperados
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])
        self.assertNotIn('client_secret', response.data)

class CrearEstudianteAPIViewTest(APITestCase):

    def setUp(self):
        # Crear un usuario para la prueba
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('crear_estudiante')  # URL de la vista a probar

        # Obtener el token JWT para el usuario
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.token = response.data['access']

    @patch('stripe.PaymentIntent.create')
    def test_crear_estudiante_y_pago(self, mock_create_payment_intent):
        # Mock de la creación de payment_intent de Stripe
        mock_create_payment_intent.return_value = {'id': 'pi_test_123', 'client_secret': 'test_secret'}

        # Datos a enviar, incluyendo una imagen de perfil mockeada
        data = {
            'nombre': 'Estudiante Test',
            'dni': '12345678',
            'fecha_nacimiento': '2000-01-01',
            'grado': 'Grado 1',
            'direccion': 'Direccion 1',
        }

        # Si estás subiendo una imagen, puedes usar `SimpleUploadedFile` para simular la carga del archivo
        from django.core.files.uploadedfile import SimpleUploadedFile
        photo = SimpleUploadedFile('foto.jpg', b'file_content', content_type='image/jpeg')
        data['foto_perfil'] = photo

        # Hacer la solicitud POST con el token de autenticación en el encabezado y los datos correctos
        response = self.client.post(self.url, data, format='multipart', HTTP_AUTHORIZATION='Bearer ' + self.token)

        # Verificar que la creación del estudiante fue exitosa
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('client_secret', response.data)

        # Verificar que se haya creado el estudiante y el pago
        estudiante = Estudiante.objects.get(dni='12345678')
        self.assertEqual(estudiante.nombre, 'Estudiante Test')

        matricula = Matricula.objects.get(estudiante=estudiante)
        self.assertEqual(matricula.monto, 100.00)

        pago = Pago.objects.get(matricula=matricula)
        self.assertEqual(pago.estado, 'Pendiente')
        self.assertEqual(pago.stripe_payment_intent_id, 'pi_test_123')



class ConfirmarPagoAPIViewTest(APITestCase):
    def setUp(self):
        # Crear un usuario y un estudiante asociado
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.estudiante = Estudiante.objects.create(
            usuario=self.user,
            nombre="Test Estudiante",
            dni="12345678",
            fecha_nacimiento="2000-01-01",
            grado="Grado 1",
            direccion="Direccion 1"
        )
        self.matricula = Matricula.objects.create(
            estudiante=self.estudiante,
            curso="Curso Ejemplo",
            monto=100.00
        )
        self.pago = Pago.objects.create(
            matricula=self.matricula,
            estado="Pendiente",
            stripe_payment_intent_id="pi_test_123"
        )
        self.url = reverse('confirmar_pago', args=[self.pago.stripe_payment_intent_id])

        # Obtener el token JWT para el usuario
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.token = response.data['access']

    @patch('stripe.PaymentIntent.retrieve')
    def test_confirmar_pago_exitoso(self, mock_retrieve):
        # Mock del stripe PaymentIntent para simular un pago exitoso
        mock_retrieve.return_value = {'status': 'succeeded'}

        # Hacer la solicitud POST con el token de autenticación en el encabezado
        response = self.client.post(self.url, HTTP_AUTHORIZATION='Bearer ' + self.token)

        # Verificar que la respuesta es correcta y el pago fue confirmado
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Pago confirmado exitosamente.")

        # Verificar que el estado de la matrícula y el pago se actualizaron
        self.pago.refresh_from_db()
        self.matricula.refresh_from_db()
        self.assertEqual(self.pago.estado, 'Completado')
        self.assertEqual(self.matricula.estado, 'Pagado')

    @patch('stripe.PaymentIntent.retrieve')
    def test_confirmar_pago_no_completado(self, mock_retrieve):
        # Mock del stripe PaymentIntent para simular un pago fallido
        mock_retrieve.return_value = {'status': 'failed'}

        # Hacer la solicitud POST con el token de autenticación en el encabezado
        response = self.client.post(self.url, HTTP_AUTHORIZATION='Bearer ' + self.token)

        # Verificar que la respuesta es un error porque el pago no está completado
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "El pago no está completado.")