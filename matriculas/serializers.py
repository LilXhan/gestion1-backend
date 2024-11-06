from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Estudiante, Matricula, Pago

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User(username=validated_data['username'], email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()
        return user

class EstudianteSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(read_only=True)  # Configurado como solo lectura

    class Meta:
        model = Estudiante
        fields = ['usuario', 'nombre', 'dni', 'fecha_nacimiento', 'grado', 'direccion', 'certificado_estudios']

class MatriculaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matricula
        fields = '__all__'

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'
