import stripe
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Estudiante, Matricula, Pago, PerfilUsuario
from .serializers import RegisterSerializer, EstudianteSerializer, UsuarioSerializer, PerfilUsuarioSerializer, MatriculaSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework import viewsets

stripe.api_key = settings.STRIPE_SECRET_KEY

class VerificarEstudianteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            estudiante = Estudiante.objects.get(usuario=request.user)
            serializer = EstudianteSerializer(estudiante)
            matricula = Matricula.objects.filter(estudiante=estudiante).first()
            
            if matricula:
                pago = Pago.objects.filter(matricula=matricula, estado='Pendiente').first()
                if pago:
                    payment_intent = stripe.PaymentIntent.retrieve(pago.stripe_payment_intent_id)
                    return Response({
                        "exists": True,
                        "estudiante": serializer.data,
                        "client_secret": payment_intent['client_secret'] 
                    })

            return Response({"exists": True, "estudiante": serializer.data})

        except Estudiante.DoesNotExist:
            return Response({"exists": False})
    
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        user_serializer = self.get_serializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        
        user = user_serializer.save()
        
        perfil_data = {}
        if 'foto_perfil' in request.data:
            perfil_data['foto_perfil'] = request.data['foto_perfil']
        
        perfil_serializer = PerfilUsuarioSerializer(data=perfil_data)
        if perfil_serializer.is_valid():
            perfil_serializer.save(usuario=user)
        
        headers = self.get_success_headers(user_serializer.data)
        return Response(user_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CrearEstudianteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        data = request.data
        serializer = EstudianteSerializer(data=data)

        if serializer.is_valid():
            estudiante = serializer.save(usuario=request.user)
            matricula = Matricula.objects.create(estudiante=estudiante, curso="Curso Ejemplo", monto=100.00)
            
            intent = stripe.PaymentIntent.create(
                amount=int(matricula.monto * 100),
                currency='usd',
                metadata={'matricula_id': matricula.id}
            )

            Pago.objects.create(matricula=matricula, stripe_payment_intent_id=intent['id'])

            return Response({
                'client_secret': intent['client_secret'],
                'payment_intent_id': intent['id']
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckStudentStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        estudiante = Estudiante.objects.filter(usuario=request.user).first()
        if estudiante:
            matricula = Matricula.objects.filter(estudiante=estudiante).first()
            if matricula:
                pago = Pago.objects.filter(matricula=matricula).first()
                estado = "rechazada" if matricula.estado == "Rechazado" else None
                return Response({
                    "has_student": True,
                    "matricula_rechazada": estado == "rechazada",
                    "payment_completed": pago.estado == "Completado" if pago else False,
                    "client_secret": stripe.PaymentIntent.retrieve(pago.stripe_payment_intent_id).client_secret if pago else None
                })
        return Response({"has_student": False}, status=200)
    
class ConfirmarPagoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_intent_id):
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent['status'] == 'succeeded':
                pago = Pago.objects.get(stripe_payment_intent_id=payment_intent_id)
                pago.estado = 'Completado'
                pago.save()

                matricula = pago.matricula
                matricula.estado = 'Pagado'
                matricula.save()

                return Response({"message": "Pago confirmado exitosamente."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "El pago no está completado."}, status=status.HTTP_400_BAD_REQUEST)

        except Pago.DoesNotExist:
            return Response({"error": "Pago no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    user = request.user

    if request.method == 'GET':
        serializer = UsuarioSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
        
        perfil_serializer = PerfilUsuarioSerializer(perfil, data=request.data, partial=True)
        if perfil_serializer.is_valid():
            perfil_serializer.save()
            
            if 'username' in request.data:
                user.username = request.data['username']
                user.save()
                
            return Response(perfil_serializer.data, status=status.HTTP_200_OK)
        
        return Response(perfil_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class MatriculaViewSet(viewsets.ModelViewSet):
    queryset = Matricula.objects.all()
    serializer_class = MatriculaSerializer

    def get_permissions(self):
        if self.action in ['list', 'verificar']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        return super().get_permissions()

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAdminUser])
    def verificar(self, request, pk=None):
        matricula = self.get_object()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado in ['Aprobado', 'Rechazado', 'Pendiente']:
            matricula.estado = nuevo_estado
            matricula.save()
            return Response({"message": "Estado de la matrícula actualizado"}, status=status.HTTP_200_OK)
        return Response({"error": "Estado no válido"}, status=status.HTTP_400_BAD_REQUEST)
    
class UserRoleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = 'authenticated' 
        if user.is_staff:
            role = 'is_staff'
        elif user.is_superuser:
            role = 'is_admin'
        
        return Response({"role": role})
    
class MatriculaListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        matriculas = Matricula.objects.all()
        serializer = MatriculaSerializer(matriculas, many=True)
        return Response(serializer.data)