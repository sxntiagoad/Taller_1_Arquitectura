from abc import ABC, abstractmethod
from django.core.mail import send_mail
from django.conf import settings

class Observer(ABC):
    """Interfaz base para todos los observadores"""
    @abstractmethod
    def update(self, evento, datos):
        pass

class Subject(ABC):
    """Clase base para sujetos observables"""
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        """Agregar un observador"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer):
        """Remover un observador"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, evento, datos):
        """Notificar a todos los observadores"""
        for observer in self._observers:
            observer.update(evento, datos)

class NotificacionConsoleObserver(Observer):
    """Observer que muestra notificaciones en consola (para desarrollo)"""
    def update(self, evento, datos):
        if evento == 'solicitud_enviada':
            print(f"📤 Nueva solicitud de amistad de {datos['remitente'].nombres} para {datos['destinatario'].nombres}")
        elif evento == 'solicitud_aceptada':
            print(f"✅ {datos['destinatario'].nombres} aceptó la solicitud de amistad de {datos['remitente'].nombres}")
        elif evento == 'solicitud_rechazada':
            print(f"❌ {datos['destinatario'].nombres} rechazó la solicitud de amistad de {datos['remitente'].nombres}")

class NotificacionEmailObserver(Observer):
    """Observer que envía notificaciones por email"""
    def update(self, evento, datos):
        if evento == 'solicitud_enviada':
            self._enviar_email_solicitud(datos)
        elif evento == 'solicitud_aceptada':
            self._enviar_email_aceptacion(datos)
    
    def _enviar_email_solicitud(self, datos):
        try:
            send_mail(
                subject='Nueva solicitud de amistad - EAFinders',
                message=f'Hola {datos["destinatario"].nombres},\n\n'
                       f'{datos["remitente"].nombres} {datos["remitente"].apellidos} '
                       f'te ha enviado una solicitud de amistad en EAFinders.\n\n'
                       f'Ingresa a la plataforma para aceptar o rechazar la solicitud.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[datos['destinatario'].email_institucional],
                fail_silently=True,
            )
            print(f"📧 Email enviado a {datos['destinatario'].email_institucional}")
        except Exception as e:
            print(f"Error enviando email: {e}")
    
    def _enviar_email_aceptacion(self, datos):
        try:
            send_mail(
                subject='Solicitud de amistad aceptada - EAFinders',
                message=f'Hola {datos["remitente"].nombres},\n\n'
                       f'{datos["destinatario"].nombres} {datos["destinatario"].apellidos} '
                       f'ha aceptado tu solicitud de amistad en EAFinders.\n\n'
                       f'¡Ya pueden comenzar a interactuar como amigos!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[datos['remitente'].email_institucional],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error enviando email: {e}")

class AmistadSubject(Subject):
    """Subject específico para manejar eventos de amistad"""
    
    def enviar_solicitud(self, user1, user2):
        """Envía una solicitud de amistad y notifica a observadores"""
        from .models import Amistad
        from django.db.models import Q
        
        # Verificar que no exista una amistad ya
        if Amistad.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        ).exists():
            raise ValueError("Ya existe una solicitud o amistad entre estos usuarios")
        
        # Crear la solicitud
        amistad = Amistad.objects.create(user1=user1, user2=user2, estado='pendiente')
        
        # Notificar a observadores
        self.notify('solicitud_enviada', {
            'remitente': user1,
            'destinatario': user2,
            'amistad': amistad
        })
        
        return amistad
    
    def aceptar_solicitud(self, amistad):
        """Acepta una solicitud de amistad y notifica"""
        amistad.estado = 'aceptada'
        amistad.save()
        
        self.notify('solicitud_aceptada', {
            'remitente': amistad.user1,
            'destinatario': amistad.user2,
            'amistad': amistad
        })
        
        return amistad
    
    def rechazar_solicitud(self, amistad):
        """Rechaza una solicitud de amistad y notifica"""
        amistad.estado = 'rechazada'
        amistad.save()
        
        self.notify('solicitud_rechazada', {
            'remitente': amistad.user1,
            'destinatario': amistad.user2,
            'amistad': amistad
        })
        
        return amistad

# Instancia global del subject con observadores simplificados
amistad_subject = AmistadSubject()
amistad_subject.attach(NotificacionConsoleObserver())
amistad_subject.attach(NotificacionEmailObserver())