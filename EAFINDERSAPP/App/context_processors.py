from .models import Amistad  # Asegúrate de que la importación es correcta

def notificaciones(request):
    if request.user.is_authenticated:
        # Solo solicitudes de amistad pendientes
        solicitudes_pendientes = Amistad.objects.filter(
            user2=request.user,
            estado='pendiente'
        ).count()
        
        return {
            'solicitudes_pendientes': solicitudes_pendientes,
        }
    return {}
