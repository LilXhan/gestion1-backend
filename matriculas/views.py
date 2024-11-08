import stripe
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Estudiante, Matricula, Pago, PerfilUsuario
from .serializers import RegisterSerializer, EstudianteSerializer, UsuarioSerializer, PerfilUsuarioSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes

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
                    # Recuperar el PaymentIntent en Stripe para obtener el `client_secret`
                    payment_intent = stripe.PaymentIntent.retrieve(pago.stripe_payment_intent_id)
                    return Response({
                        "exists": True,
                        "estudiante": serializer.data,
                        "client_secret": payment_intent['client_secret']  # Devolver el `client_secret` correcto
                    })

            return Response({"exists": True, "estudiante": serializer.data})

        except Estudiante.DoesNotExist:
            return Response({"exists": False})

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]  # Agregar soporte para archivos

    def post(self, request, *args, **kwargs):
        user_serializer = self.get_serializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        
        # Crear el usuario
        user = user_serializer.save()
        
        # Crear el perfil de usuario y asignar la foto de perfil si se proporciona
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_student(request):
    estudiante = Estudiante.objects.filter(usuario=request.user).first()
    if estudiante:
        matricula = Matricula.objects.filter(estudiante=estudiante).first()
        
        if matricula:
            pago = Pago.objects.filter(matricula=matricula).first()
            if pago and pago.estado == 'Completado':
                return Response({"has_student": True, "payment_completed": True}, status=200)
            elif pago and pago.estado == 'Pendiente':
                # Recuperar el PaymentIntent en Stripe para obtener el `client_secret`
                payment_intent = stripe.PaymentIntent.retrieve(pago.stripe_payment_intent_id)
                return Response({"has_student": True, "payment_completed": False, "client_secret": payment_intent['client_secret']}, status=200)

        return Response({"has_student": True, "payment_completed": False}, status=200)
    else:
        return Response({"has_student": False}, status=200)
    
class ConfirmarPagoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_intent_id):
        try:
            # Verificar el estado del PaymentIntent en Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent['status'] == 'succeeded':
                # Obtener el pago y la matrícula relacionados
                pago = Pago.objects.get(stripe_payment_intent_id=payment_intent_id)
                pago.estado = 'Completado'
                pago.save()

                # Actualizar el estado de la matrícula a 'Pagado'
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
        
        # Actualizar el perfil del usuario
        perfil_serializer = PerfilUsuarioSerializer(perfil, data=request.data, partial=True)
        if perfil_serializer.is_valid():
            perfil_serializer.save()
            
            # También actualizar el nombre de usuario si está en los datos
            if 'username' in request.data:
                user.username = request.data['username']
                user.save()
                
            return Response(perfil_serializer.data, status=status.HTTP_200_OK)
        
        return Response(perfil_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
