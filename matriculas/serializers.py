from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Estudiante, Matricula, Pago, PerfilUsuario

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    foto_perfil = serializers.ImageField(write_only=True, required=False)  # Foto de perfil opcional en el registro

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'foto_perfil']

    def create(self, validated_data):
        # Extraer la foto de perfil si está en los datos
        foto_perfil = validated_data.pop('foto_perfil', None)
        user = User(username=validated_data['username'], email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()

        # Crear el perfil y asignar la foto de perfil
        PerfilUsuario.objects.create(usuario=user, foto_perfil=foto_perfil)
        
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
        
class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ['foto_perfil']

class UsuarioSerializer(serializers.ModelSerializer):
    perfil = PerfilUsuarioSerializer(read_only=True)  # Incluye el perfil en la respuesta

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'perfil']