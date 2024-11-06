from django.db import models
from django.contrib.auth.models import User

class Estudiante(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=8)  # Documento de identidad peruano
    fecha_nacimiento = models.DateField()
    grado = models.CharField(max_length=50)  # Grado académico
    direccion = models.TextField()
    certificado_estudios = models.FileField(upload_to='certificados/', null=True, blank=True)  # Campo de archivo

    def __str__(self):
        return self.nombre

class Matricula(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    curso = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    estado = models.CharField(max_length=20, default='Pendiente')  # Pendiente o Pagado

class Pago(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=20, default='Pendiente')
