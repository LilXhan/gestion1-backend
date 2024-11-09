from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Estudiante, Matricula, Pago, PerfilUsuario

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    foto_perfil = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'foto_perfil']

    def create(self, validated_data):
        foto_perfil = validated_data.pop('foto_perfil', None)
        user = User(username=validated_data['username'], email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()

        PerfilUsuario.objects.create(usuario=user, foto_perfil=foto_perfil)
        
        return user

class EstudianteSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(read_only=True) 

    class Meta:
        model = Estudiante
        fields = ['usuario', 'nombre', 'dni', 'fecha_nacimiento', 'grado', 'direccion', 'certificado_estudios']

class MatriculaSerializer(serializers.ModelSerializer):
    estudiante = EstudianteSerializer(read_only=True)  
    pago = serializers.SerializerMethodField()  

    class Meta:
        model = Matricula
        fields = ['id', 'curso', 'monto', 'estado', 'estudiante', 'pago']

    def get_pago(self, obj):
        pago = Pago.objects.filter(matricula=obj).first()
        return PagoSerializer(pago).data if pago else None

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'
        
class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ['foto_perfil']

class UsuarioSerializer(serializers.ModelSerializer):
    perfil = PerfilUsuarioSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'perfil']