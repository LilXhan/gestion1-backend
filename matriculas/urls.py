from django.urls import path
from .views import RegisterAPIView, CrearEstudianteAPIView,  VerificarEstudianteAPIView, check_student # CrearMatriculaAPIView, CrearPagoAPIView, ConfirmarPagoAPIView,

urlpatterns = [
    path('registro/', RegisterAPIView.as_view(), name='registro'),
    path('estudiante/crear/', CrearEstudianteAPIView.as_view(), name='crear_estudiante'),
    # path('matricula/crear/', CrearMatriculaAPIView.as_view(), name='crear_matricula'),
    # path('pago/crear/<int:matricula_id>/', CrearPagoAPIView.as_view(), name='crear_pago'),
    # path('pago/confirmar/<str:payment_intent_id>/', ConfirmarPagoAPIView.as_view(), name='confirmar_pago'),
    path('estudiante/verificar/', VerificarEstudianteAPIView.as_view(), name='verificar_estudiante'),
    path('check-student/', check_student, name='check_student'),

]
