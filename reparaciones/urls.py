from django.urls import path
from . import views

app_name = 'reparaciones'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('crear/', views.crear_orden, name='crear_orden'),
    path('crear-repuesto/', views.crear_repuesto, name='crear_repuesto'), # <-- Nueva Ruta
    path('actualizar/<int:orden_id>/', views.actualizar_orden, name='actualizar_orden'),
    path('actualizar-cliente/<int:cliente_id>/', views.actualizar_cliente, name='actualizar_cliente'),
    path('cambiar-estado/<int:orden_id>/<str:nuevo_estado>/', views.cambiar_estado, name='cambiar_estado'),
    path('entregar/<int:orden_id>/', views.entregar_orden, name='entregar_orden'),
]