from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import ForoCreateView, ForoDetailView, ForoListView

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('registro/', views.registro_usuario, name='register'),
    path('login/', views.login, name='login'),
    path('api/logout/', views.logout_user, name='logout'),
    path('Cuenta/', views.account, name='Cuenta'),
    path('EditProfile/', views.EditProfile, name='EditProfile'),
    path('profile/<int:user_id>/', views.profile_view, name='profile'),
    path('Notificaciones/', views.Notificaciones, name='Notificaciones'),
    path('buscar/', views.buscar_usuarios, name='buscar_usuarios'),
    path('enviar_solicitud_amistad/<int:user_id>/', views.enviar_solicitud_amistad, name='enviar_solicitud_amistad'),
    path('aceptar_solicitud_amistad/<int:solicitud_id>/', views.aceptar_solicitud_amistad, name='aceptar_solicitud'),
    path('rechazar_solicitud_amistad/<int:solicitud_id>/', views.rechazar_solicitud_amistad, name='rechazar_solicitud'),
    path('eliminar_amistad/<int:user_id>/', views.eliminar_amistad, name='eliminar_amistad'),
    path('conversaciones/', views.lista_conversaciones, name='lista_conversaciones'),
    path('chat/<int:amigo_id>/', views.chat_view, name='chat_view'),
    path('chat/<int:amigo_id>/obtener-mensajes/', views.obtener_mensajes, name='obtener_mensajes'),

    path('crear_foro/', ForoCreateView.as_view(), name='crear_foro'),
    path('foro/<int:foro_id>/', ForoDetailView.as_view(), name='detalle_foro'),
    path('foros/', ForoListView.as_view(), name='lista_foros'),

    path('foros/<int:foro_id>/like/', views.like_foro, name='like_foro'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
