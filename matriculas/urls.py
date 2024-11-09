from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterAPIView, UserRoleAPIView, MatriculaViewSet, MatriculaListAPIView, CrearEstudianteAPIView,  VerificarEstudianteAPIView, CheckStudentStatusAPIView, perfil_usuario, ConfirmarPagoAPIView # CrearMatriculaAPIView, CrearPagoAPIView, ConfirmarPagoAPIView,

router = DefaultRouter()
router.register(r'', MatriculaViewSet)

urlpatterns = [
    path('registro/', RegisterAPIView.as_view(), name='registro'),
    path('estudiante/crear/', CrearEstudianteAPIView.as_view(), name='crear_estudiante'),
    path('estudiante/verificar/', VerificarEstudianteAPIView.as_view(), name='verificar_estudiante'),
    path('check-student/', CheckStudentStatusAPIView.as_view(), name='check_student'),
    path('pago/confirmar/<str:payment_intent_id>/', ConfirmarPagoAPIView.as_view(), name='confirmar_pago'),
    path('perfil/', perfil_usuario, name='perfil_usuario'),
    path('role/', UserRoleAPIView.as_view(), name='user_role'),  
    path('', MatriculaListAPIView.as_view(), name='matricula_list'), 
    path('', include(router.urls)),

]
