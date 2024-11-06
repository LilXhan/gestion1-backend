import stripe
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Estudiante, Matricula, Pago
from .serializers import RegisterSerializer, EstudianteSerializer, MatriculaSerializer, PagoSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

stripe.api_key = settings.STRIPE_SECRET_KEY

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class CrearEstudianteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # Usamos request.data directamente sin modificarlo
        serializer = EstudianteSerializer(data=request.data)

        if serializer.is_valid():
            # Guardamos el estudiante y asignamos el usuario autenticado
            estudiante = serializer.save(usuario=request.user)
            
            # Crear la matrícula y el pago en Stripe
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

        # Imprimir errores de validación para depuración y retornarlos en la respuesta
        print("Errores de validación:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CrearMatriculaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        estudiante = Estudiante.objects.get(usuario=request.user)
        matricula = Matricula.objects.create(estudiante=estudiante, curso="Curso Ejemplo")
        serializer = MatriculaSerializer(matricula)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CrearPagoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, matricula_id):
        matricula = Matricula.objects.get(id=matricula_id, estudiante__usuario=request.user)
        intent = stripe.PaymentIntent.create(
            amount=int(matricula.monto * 100),  # En centavos
            currency='usd',
            metadata={'matricula_id': matricula.id}
        )
        Pago.objects.create(matricula=matricula, stripe_payment_intent_id=intent['id'])
        return Response({'client_secret': intent['client_secret']}, status=status.HTTP_200_OK)

class ConfirmarPagoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_intent_id):
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.status == 'succeeded':
            pago = Pago.objects.get(stripe_payment_intent_id=payment_intent_id)
            pago.estado = 'Pagado'
            pago.save()
            matricula = pago.matricula
            matricula.estado = 'Pagado'
            matricula.save()
            return Response({'message': 'Pago completado con éxito'}, status=status.HTTP_200_OK)
        return Response({'error': 'Pago no completado'}, status=status.HTTP_400_BAD_REQUEST)
