from abc import ABC, abstractmethod
from .models import Usuario, Amistad, Mensaje, Foro, Comentario, Etiqueta
from django.contrib.auth import login as auth_login, authenticate, logout
from .forms import RegistroUsuarioForm, LoginForm, EditarPerfilForm, BuscarUsuarioForm, ForoForm, ComentarioForm
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .observers import amistad_subject
from django.views.generic import CreateView, DetailView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

def logout_user(request):
    """View to log out the user."""
    if request.method == 'POST':
        logout(request)
        return redirect('login')  # Redirect to the login page
    return redirect('home')  # If not POST, redirect to home or another page

@login_required
def profile_view(request, user_id):
    profile_user = get_object_or_404(Usuario, id=user_id)

    # Verifica si ya hay una solicitud enviada o recibida
    solicitud_enviada = Amistad.objects.filter(user1=request.user, user2=profile_user, estado='pendiente').exists()
    solicitud_recibida = Amistad.objects.filter(user1=profile_user, user2=request.user, estado='pendiente').first()
    son_amigos = Amistad.objects.filter(
        (Q(user1=request.user) & Q(user2=profile_user)) |
        (Q(user1=profile_user) & Q(user2=request.user)),
        estado='aceptada'
    ).exists()

    contexto = {
        'profile_user': profile_user,
        'solicitud_enviada': solicitud_enviada,
        'solicitud_recibida': solicitud_recibida,  # Pasamos la solicitud recibida si existe
        'son_amigos': son_amigos,
    }

    return render(request, 'Profiles.html', contexto)


@login_required
def account(request):
    # Obtener las amistades donde el usuario sea user1 o user2 y la solicitud haya sido aceptada
    amistades = Amistad.objects.filter(
        Q(user1=request.user, estado='aceptada') | Q(user2=request.user, estado='aceptada')
    )

    amigos = []
    for amistad in amistades:
        # Si el usuario es user1, el amigo es user2, y viceversa
        if amistad.user1 == request.user:
            amigos.append(amistad.user2)
        else:
            amigos.append(amistad.user1)

    return render(request, 'Cuenta.html', {'amigos': amigos})


def home(request):
    """View to display home page with all users except the logged-in user."""
    users = Usuario.objects.exclude(id=request.user.id)
    return render(request, 'home.html', {'users': users})

@login_required
def EditProfile(request):
    usuario = request.user  # Get the current user

    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()  # Save the changes
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('Cuenta')  # Redirect to user profile
        else:
            messages.error(request, 'Por favor corrige los errores a continuación.')
    else:
        form = EditarPerfilForm(instance=usuario)  # Initialize the form with the current user data

    return render(request, 'EditProfile.html', {'form': form})

def login(request):
    """View for user login."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email_institucional = form.cleaned_data['email_institucional']
            password = form.cleaned_data['password']

            # Authenticate using the email as the username
            usuario = authenticate(request, username=email_institucional, password=password)
            if usuario is not None:
                auth_login(request, usuario)
                return redirect('home')
            else:
                messages.error(request, "Correo o contraseña incorrectos.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def registro_usuario(request):
    """View for user registration."""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.password = make_password(form.cleaned_data['password'])  # Hash the password
            usuario.save()

            # Automatically authenticate the user after registration
            auth_login(request, usuario)
            return redirect('home')  # Redirect to the home page
    else:
        form = RegistroUsuarioForm()

    return render(request, 'Register.html', {'form': form})

# abstraccion de alto nivel solo depende de la interfaz
class IUsuarioRepository(ABC):
    @abstractmethod
    def get_all(self):
        pass
    
    @abstractmethod
    def filter_by_query(self, queryset, query):
        pass
    
    @abstractmethod
    def filter_by_carrera(self, queryset, carrera):
        pass
    
    @abstractmethod
    def filter_by_semestre(self, queryset, semestre):
        pass

# servicio de alto nivel solo depende de la abstraccion
class UsuarioSearchService:
    def __init__(self, usuario_repository: IUsuarioRepository):
        self.usuario_repository = usuario_repository

    def buscar_usuarios(self, query=None, carrera=None, semestre=None):
        usuarios = self.usuario_repository.get_all()

        if query:
            usuarios = self.usuario_repository.filter_by_query(usuarios, query)
        if carrera:
            usuarios = self.usuario_repository.filter_by_carrera(usuarios, carrera)
        if semestre:
            usuarios = self.usuario_repository.filter_by_semestre(usuarios, semestre)
        return usuarios

# implementacion concreta de bajo nivel que solo depende de la abstraccion
class DjangoUsuarioRepository(IUsuarioRepository):
    def get_all(self):
        return Usuario.objects.all()
    
    def filter_by_query(self, queryset, query):
        return queryset.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(email_institucional__icontains=query)
        )
    
    def filter_by_carrera(self, queryset, carrera):
        return queryset.filter(carrera=carrera)
    
    def filter_by_semestre(self, queryset, semestre):
        return queryset.filter(semestre=semestre)

# vista que inyecta las dependencias
def buscar_usuarios(request):
    form = BuscarUsuarioForm(request.GET)
    
    # inversion de dependencias: el modulo de alto nivel recibe la implementacion
    usuario_repository = DjangoUsuarioRepository()  # implementacion concreta
    search_service = UsuarioSearchService(usuario_repository)  # inyeccion
    
    usuarios = Usuario.objects.all()  # default
    
    if form.is_valid():
        usuarios = search_service.buscar_usuarios(
            query=form.cleaned_data.get('query'),
            carrera=form.cleaned_data.get('carrera'),
            semestre=form.cleaned_data.get('semestre')
        )
    
    return render(request, 'buscar_usuarios.html', {'form': form, 'usuarios': usuarios}) 


@login_required
def enviar_solicitud_amistad(request, user_id):
    """Vista para enviar solicitud de amistad usando el patrón Observer"""
    user_destino = get_object_or_404(Usuario, id=user_id)
    
    if request.user == user_destino:
        messages.error(request, 'No puedes enviarte una solicitud de amistad a ti mismo')
        return redirect('profile', user_id=user_id)
    
    try:
        # Usar el subject para enviar la solicitud
        amistad_subject.enviar_solicitud(request.user, user_destino)
        messages.success(request, f'Solicitud de amistad enviada a {user_destino.nombres}')
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('profile', user_id=user_id)

@login_required
def aceptar_solicitud_amistad(request, solicitud_id):  # ✅ Cambiar de amistad_id a solicitud_id
    """Vista para aceptar solicitud de amistad usando el patrón Observer"""
    amistad = get_object_or_404(Amistad, id=solicitud_id, user2=request.user, estado='pendiente')
    
    try:
        # Usar el subject para aceptar la solicitud
        amistad_subject.aceptar_solicitud(amistad)
        messages.success(request, f'Solicitud de amistad de {amistad.user1.nombres} aceptada')
    except Exception as e:
        messages.error(request, f'Error al aceptar solicitud: {str(e)}')
    
    return redirect('Notificaciones')

@login_required
def rechazar_solicitud_amistad(request, solicitud_id):  # ✅ Cambiar de amistad_id a solicitud_id
    """Vista para rechazar solicitud de amistad usando el patrón Observer"""
    amistad = get_object_or_404(Amistad, id=solicitud_id, user2=request.user, estado='pendiente')
    
    try:
        # Usar el subject para rechazar la solicitud
        amistad_subject.rechazar_solicitud(amistad)
        messages.success(request, f'Solicitud de amistad de {amistad.user1.nombres} rechazada')
    except Exception as e:
        messages.error(request, f'Error al rechazar solicitud: {str(e)}')
    
    return redirect('Notificaciones')

@login_required
def eliminar_amistad(request, user_id):
    amigo = get_object_or_404(Usuario, id=user_id)
    amistad = Amistad.objects.filter(
        (Q(user1=request.user) & Q(user2=amigo)) | (Q(user1=amigo) & Q(user2=request.user))
    )
    if amistad.exists():
        amistad.delete()
        messages.success(request, f'Amistad eliminada con {amigo}.')
    else:
        messages.error(request, 'No tienes una amistad con este usuario.')

    return redirect('profile', user_id=user_id)

@login_required
def Notificaciones(request):
    # Solo solicitudes de amistad pendientes
    solicitudes = Amistad.objects.filter(user2=request.user, estado='pendiente')
    
    contexto = {
        'solicitudes': solicitudes,
    }
    return render(request, 'Notificaciones.html', contexto)
@login_required
def chat_view(request, amigo_id):
    amigo = get_object_or_404(Usuario, id=amigo_id)

    # Verificar que son amigos
    amistad = Amistad.objects.filter(
        (Q(user1=request.user) & Q(user2=amigo)) | (Q(user1=amigo) & Q(user2=request.user)),
        estado='aceptada'
    ).exists()

    if not amistad:
        return redirect('home')  # Redirigir si no son amigos

    # Obtener los mensajes entre el usuario actual y el amigo
    mensajes = Mensaje.objects.filter(
        Q(remitente=request.user, destinatario=amigo) | Q(remitente=amigo, destinatario=request.user)
    ).order_by('fecha_enviado')

    if request.method == 'POST':
        contenido = request.POST.get('contenido')
        if contenido:
            Mensaje.objects.create(remitente=request.user, destinatario=amigo, contenido=contenido)
            return redirect('chat_view', amigo_id=amigo.id)  # Redirigir para actualizar la conversación

    return render(request, 'chat.html', {'amigo': amigo, 'mensajes': mensajes})


@login_required
def obtener_mensajes(request, amigo_id):
    amigo = get_object_or_404(Usuario, id=amigo_id)

    # Obtener mensajes entre el usuario actual y el amigo
    mensajes = Mensaje.objects.filter(
        Q(remitente=request.user, destinatario=amigo) | Q(remitente=amigo, destinatario=request.user)
    ).order_by('fecha_enviado')

    # Formatear los mensajes para JSON
    mensajes_json = []
    for mensaje in mensajes:
        mensajes_json.append({
            'remitente': mensaje.remitente.nombres,  # Asegúrate de que este campo exista en tu modelo
            'contenido': mensaje.contenido,
        })

    return JsonResponse(mensajes_json, safe=False)
@login_required
def lista_conversaciones(request):
    # Obtener amigos con los que tienes amistad aceptada
    amigos = Amistad.objects.filter(
        (Q(user1=request.user) | Q(user2=request.user)),
        estado='aceptada'
    )
    return render(request, 'lista_Chats.html', {'amigos': amigos})


class ForoCreateView(LoginRequiredMixin, CreateView):
    model = Foro
    form_class = ForoForm
    template_name = "crear_foro.html"
    success_url = reverse_lazy("lista_foros")

    def form_valid(self, form):
        form.instance.creador = self.request.user
        return super().form_valid(form)


class ForoDetailView(DetailView):
    model = Foro
    pk_url_kwarg = "foro_id"  # Para mantener compatibilidad con tu URL
    template_name = "detalle_foro.html"
    context_object_name = "foro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        foro = self.object
        context["comentarios"] = foro.comentarios.filter(parent=None).order_by("-fecha_creacion")
        context["form"] = ComentarioForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ComentarioForm(request.POST, request.FILES)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.foro = self.object
            comentario.autor = request.user

            parent_id = request.POST.get("parent_id")
            if parent_id:
                comentario.parent = Comentario.objects.get(id=parent_id)

            comentario.save()
            return redirect("detalle_foro", foro_id=self.object.id)

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class ForoListView(ListView):
    model = Foro
    template_name = "lista_foros.html"
    context_object_name = "foros"

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        etiquetas_ids = self.request.GET.getlist("etiquetas")

        if query:
            qs = qs.filter(
                Q(titulo__icontains=query) |
                Q(creador__nombres__icontains=query) |
                Q(creador__apellidos__icontains=query) |
                Q(fecha_creacion__icontains=query)
            )

        if etiquetas_ids:
            etiquetas_q = Q()
            for etiqueta_id in etiquetas_ids:
                etiquetas_q |= Q(etiquetas__id=etiqueta_id)
            qs = qs.filter(etiquetas_q).distinct()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["etiquetas"] = Etiqueta.objects.all()
        return context

@login_required
def like_foro(request, foro_id):
    foro = get_object_or_404(Foro, id=foro_id)
    usuario = request.user

    if usuario in foro.likes.all():
        foro.likes.remove(usuario)  # Quitar el like si ya lo ha dado
    else:
        foro.likes.add(usuario)  # Añadir el like

    return redirect('lista_foros')

