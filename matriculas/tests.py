
import pytest
from django.contrib.auth.models import User
from matriculas.models import Estudiante, Matricula, Pago, PerfilUsuario
from rest_framework.test import APIClient

# PRUEBAS UNITARIAS

@pytest.mark.django_db
def test_estudiante_model():
    user = User.objects.create_user(username="testuser", password="testpass")
    estudiante = Estudiante.objects.create(
        usuario=user,
        nombre="Juan Perez",
        dni="12345678",
        fecha_nacimiento="2000-01-01",
        grado="5to Primaria",
        direccion="Calle 123"
    )
    assert str(estudiante) == "Juan Perez"

@pytest.mark.django_db
def test_matricula_model():
    user = User.objects.create_user(username="testuser", password="testpass")
    estudiante = Estudiante.objects.create(
        usuario=user,
        nombre="Juan Perez",
        dni="12345678",
        fecha_nacimiento="2000-01-01",
        grado="5to Primaria",
        direccion="Calle 123"
    )
    matricula = Matricula.objects.create(
        estudiante=estudiante,
        curso="Matemáticas",
        monto=150.50,
        estado="Pendiente"
    )
    assert str(matricula) == "Matemáticas"


# TEST DE INTEGRACION

@pytest.mark.django_db
def test_register_api():
    client = APIClient()
    response = client.post('/api/matriculas/registro/', {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass"
    })
    assert response.status_code == 201
    assert response.data["username"] == "testuser"

@pytest.mark.django_db
def test_create_estudiante_api():
    user = User.objects.create_user(username="testuser", password="testpass")
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post('/api/matriculas/estudiante/crear/', {
        "nombre": "Juan Perez",
        "dni": "12345678",
        "fecha_nacimiento": "2000-01-01",
        "grado": "5to Primaria",
        "direccion": "Calle 123"
    })
    assert response.status_code == 200
    assert "client_secret" in response.data

# TEST DE SISTEMA O END TO END

@pytest.mark.django_db
def test_end_to_end_student_creation_and_payment():
    client = APIClient()

    # Register user
    register_response = client.post('/api/matriculas/registro/', {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass"
    })
    assert register_response.status_code == 201
    user_id = register_response.data["id"]

    # Authenticate user
    user = User.objects.get(id=user_id)
    client.force_authenticate(user=user)

    # Create estudiante
    estudiante_response = client.post('/api/matriculas/estudiante/crear/', {
        "nombre": "Juan Perez",
        "dni": "12345678",
        "fecha_nacimiento": "2000-01-01",
        "grado": "5to Primaria",
        "direccion": "Calle 123"
    })
    assert estudiante_response.status_code == 200
    assert "client_secret" in estudiante_response.data

    # Check student status
    status_response = client.get('/api/matriculas/check-student/')
    assert status_response.status_code == 200
    assert status_response.data["has_student"] is True
