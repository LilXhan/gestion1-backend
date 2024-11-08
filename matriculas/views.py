import stripe
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Estudiante, Matricula, Pago
from .serializers import RegisterSerializer, EstudianteSerializer, MatriculaSerializer
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
                    return Response({
                        "exists": True,
                        "estudiante": serializer.data,
                        "client_secret": pago.stripe_payment_intent_id  # Si el pago está pendiente, devuelve el `client_secret`
                    })

            return Response({"exists": True, "estudiante": serializer.data})

        except Estudiante.DoesNotExist:
            return Response({"exists": False})

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


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
        return Response({"has_student": True, "student_id": estudiante.id}, status=200)
    else:
        return Response({"has_student": False}, status=200)