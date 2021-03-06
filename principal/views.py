from principal.models import Personal, Miembro, Proyecto, Equipo, Historia, Tarea, Sprint, Poker, ComentarioReuniones
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.validators import validate_integer
import re
from datetime import date, datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist
from forms import ProyectoForm, UserForm, HistoriaForm, TareaForm, SprintForm, SelectSprintForm, ComentarioReunionesForm

# Create your views here.

def inicio(request):
    usuario=request.user  
    if usuario.is_authenticated():    
        if usuario.is_superuser:
            try:
                personal=Personal.objects.get(usuario=usuario.id)
                miembro = Miembro.objects.get(usuario=usuario.id)
            except:
                Personal.objects.create(
                    foto = "default",
                    usuario = usuario,
                    empresa = ""
                )
                personal=Personal.objects.get(usuario=usuario.id)
                miembro = Miembro.objects.get(usuario=usuario.id)
        else:
            miembro = Miembro.objects.get(usuario=usuario.id)
            personal=Miembro.objects.get(usuario=usuario.id)
            
        try:
            rol = Equipo.objects.filter(miembro=miembro.id).first()
            equipo = Equipo.objects.filter(miembro=miembro.id)
            proyectos = Equipo.objects.filter(miembro=miembro.id)
            vproyectos = Equipo.objects.filter(miembro=miembro.id).values('proyecto_id').distinct()
            historias = Historia.objects.filter(proyecto__in=vproyectos).exclude(sprint_id=None)
            votospoker= Poker.objects.filter(jugador__in=equipo).filter(historia__in=historias)
            pendientespoker = historias.exclude(id__in=votospoker.values('historia_id'))
            tareas = Tarea.objects.filter(realizador__in=equipo).order_by('estado')
        except:
            print "no hay datos de usuario"
            return render_to_response('privado.html',{'personal':personal}, context_instance=RequestContext(request))

    if usuario.is_authenticated():
        return render_to_response('privado.html',{'rol':rol, 'equipo':equipo,'historias':pendientespoker,'tareas':tareas,'proyectos':proyectos,'personal':personal}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/ingresar')
    
    

def ingresar(request):
    if not request.user.is_anonymous():
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        formulario = AuthenticationForm(request.POST)
        if formulario.is_valid:
            usuario = request.POST['username']
            clave = request.POST['password']
            acceso = authenticate(username=usuario,password=clave)
            if acceso is not None:
                if acceso.is_active:
                    login(request, acceso)
                    return HttpResponseRedirect('/')
                else:
                    return render_to_response('noactivo.html', context_instance=RequestContext(request))
            else:
                #No existe el usuario o la contrasena no es correcta.
                validacion=1
                return render_to_response('ingresar.html',{'validacion':validacion, 'formulario':formulario}, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/noFormularioValido')
    else:
        formulario = AuthenticationForm()
    return render_to_response('ingresar.html',{'formulario':formulario}, context_instance=RequestContext(request))


def registro(request):
    if request.method == 'POST':
        formulario = UserCreationForm(request.POST)
        empresa = request.POST['empresa']
        usuario = request.POST['username']
        clave = request.POST['password1']
        clave2 = request.POST['password2']
        if not usuario or not clave or not clave2 or not empresa:
            return HttpResponseRedirect('/rellenarcampos')
        else:
            try:              
                existe = User.objects.get(username=usuario)
                #El usuario ya existe.
                validacion=1
                return render_to_response('registro.html',{'validacion':validacion, 'formulario':formulario}, context_instance=RequestContext(request))
            except:
                try:                        
                    u = formulario.save(commit=False)
                    u.is_superuser = 1
                    u.save()
                except:
                    #contrasenas diferentes
                    validacion=2
                    return render_to_response('registro.html',{'validacion':validacion, 'formulario':formulario}, context_instance=RequestContext(request))
            try:
                p = Personal.objects.create(
                    foto = "default",
                    usuario = u,
                    empresa = request.POST['empresa']
                )
                p.save()
                m = Miembro.objects.create(
                    foto = "default",
                    usuario = u,
                    jefe = p,
                    empresa = request.POST['empresa']
                )
                m.save()
              
            except:
                e = User.objects.get(username=usuario)
                e.delete()
                #Empresa ya existe
                validacion=3
                return render_to_response('registro.html',{'validacion':validacion, 'formulario':formulario}, context_instance=RequestContext(request))                  
            acceso = authenticate(username=usuario, password=clave)
            if acceso is not None:
                if acceso.is_active:
                    login(request, acceso)
                    return HttpResponseRedirect('/')
    else:
        formulario = UserCreationForm()
    return render_to_response('registro.html',{'formulario':formulario}, context_instance=RequestContext(request))

@login_required(login_url='/ingresar')
def cerrar(request):
    logout(request)
    return HttpResponseRedirect('/')

@login_required(login_url='/ingresar')
def lista_miembros(request):
    usuario=request.user
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            miembros = Miembro.objects.filter(jefe=personal.id).exclude(usuario=personal.usuario)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            miembros = Miembro.objects.filter(jefe=personal.jefe).exclude(usuario=personal.jefe.usuario)
          
    if usuario.is_authenticated():
        return render_to_response('miembros.html',{'personal':personal, 'miembros':miembros}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    

@login_required(login_url='/ingresar')   
def nuevo_miembro(request):
    usuario=request.user
    if usuario.is_authenticated():
        personal=Personal.objects.get(usuario=usuario.id)
    if request.method == 'POST':
        formulario = UserCreationForm(request.POST)

        usuario = request.POST['username']
        clave = request.POST['password1']
        clave2 = request.POST['password2']
        nombre = request.POST['first_name']
        apellidos = request.POST['last_name']
        email = request.POST['email']
        if not usuario or not clave or not clave2:
            #rellenarcampos
            validacion=1
            return render_to_response('registromiembro.html',{'nombre':nombre,'apellidos':apellidos,'email':email,'validacion':validacion, 'personal':personal,'formulario':formulario}, context_instance=RequestContext(request))
        else:
            try:              
                existe = User.objects.get(username=usuario)
                #usuario ya existe
                validacion=2
                return render_to_response('registromiembro.html',{'nombre':nombre,'apellidos':apellidos,'email':email,'validacion':validacion, 'personal':personal,'formulario':formulario}, context_instance=RequestContext(request))
            except:
                try:                        
                    u = formulario.save(commit=False)
                    u.first_name = nombre
                    u.last_name = apellidos
                    u.email = email
                    u.save()
                except:
                    #contrasenas diferentes
                    validacion=3
                    return render_to_response('registromiembro.html',{'usuario':usuario,'nombre':nombre,'apellidos':apellidos,'email':email,'validacion':validacion, 'personal':personal,'formulario':formulario}, context_instance=RequestContext(request))
            
            m = Miembro.objects.create(
                foto = "default",
                usuario = u,
                jefe = personal,
                empresa = personal.empresa
            )
            m.save()                  
            return HttpResponseRedirect('/miembros')

    else:
        formulario = UserCreationForm()
    return render_to_response('registromiembro.html',{'personal':personal,'formulario':formulario}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')   
def editar_miembro(request,id_usuario):
    usuario=request.user
    miembro = Miembro.objects.get(usuario=id_usuario)
    user = User.objects.get(id=id_usuario)

    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario)     
        else:
            personal=Miembro.objects.get(usuario=id_usuario)

    if request.method == 'POST':
        formulario = UserForm(request.POST)
        if formulario.is_valid():
            nombreuser = request.POST['username']
            clave = request.POST['password1']
            clave2 = request.POST['password2']
            nombre = request.POST['first_name']
            apellidos = request.POST['last_name']
            email = request.POST['email']
            telefono = request.POST['telefono']
            if not nombreuser:
                #Nombre usuario obligatorio
                validacion=1
                return render_to_response('editarmiembro.html',{'validacion':validacion, 'personal':personal,'miembro':miembro,'formulario':formulario}, context_instance=RequestContext(request))
            else:
                print nombreuser
                if not clave or not clave2:                  
                    user.username = nombreuser
                    user.first_name = nombre
                    user.last_name = apellidos
                    user.email = email
                    user.save()
                    if telefono:
                        miembro.telefono = telefono
                        miembro.save()
                elif clave == clave2:
                    user.username = nombreuser
                    user.set_password(clave)
                    user.first_name = nombre
                    user.last_name = apellidos
                    user.email = email
                    user.save()
                    if telefono:
                        miembro.telefono = telefono
                        miembro.save()
                else:
                    #contrasenas diferentes
                    validacion=2
                    return render_to_response('editarmiembro.html',{'validacion':validacion, 'personal':personal,'miembro':miembro,'formulario':formulario}, context_instance=RequestContext(request))          
                    
                 
                return HttpResponseRedirect('/miembros')
        else:
            print formulario.errors
            #formulario no es valido
            validacion=3
            return render_to_response('editarmiembro.html',{'validacion':validacion, 'personal':personal,'miembro':miembro,'formulario':formulario}, context_instance=RequestContext(request))
    else:
        formulario = UserForm()
    return render_to_response('editarmiembro.html',{'personal':personal,'miembro':miembro,'formulario':formulario}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def eliminar_miembro(request,id_usuario):
    usuario=request.user
    miembro = Miembro.objects.get(usuario=id_usuario)
    user = User.objects.get(id=id_usuario)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            miembros = Miembro.objects.filter(jefe=personal.id).exclude(usuario=personal.usuario)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            miembros = Miembro.objects.filter(jefe=personal.jefe).exclude(usuario=personal.jefe.usuario)
            
    miembro.delete()
    user.delete()
          
    if usuario.is_authenticated():
        return render_to_response('miembros.html',{'personal':personal, 'miembros':miembros}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))



@login_required(login_url='/ingresar')
def lista_proyectos(request):
    usuario=request.user
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyectos=Proyecto.objects.filter(jefeProyecto=personal.id)
            equipos=Equipo.objects.all()
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyectos=Equipo.objects.filter(miembro=personal.id)
            equipos=Equipo.objects.all()
          
    if usuario.is_authenticated():
        return render_to_response('proyectos.html',{'equipos':equipos,'personal':personal, 'proyectos':proyectos}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    
    
@login_required(login_url='/ingresar')
def asignar_rol(request,id_proyecto,id_equipo,id_rol):
    usuario=request.user
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyectos=Proyecto.objects.filter(jefeProyecto=personal.id)
            equipos=Equipo.objects.all()
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyectos=Equipo.objects.filter(miembro=personal.id)
            equipos=Equipo.objects.all()
          
        if id_rol=='1':  
            e = Equipo.objects.filter(proyecto_id=id_proyecto).get(pk=id_equipo)
            e.scrummaster=1
            e.teammember=0
            e.productowner=0
            e.save()
        if id_rol=='2':  
            e = Equipo.objects.filter(proyecto_id=id_proyecto).get(pk=id_equipo)
            e.scrummaster=0
            e.teammember=1
            e.productowner=0
            e.save()
        if id_rol=='3':  
            e = Equipo.objects.filter(proyecto_id=id_proyecto).get(pk=id_equipo)
            e.scrummaster=0
            e.teammember=0
            e.productowner=1
            e.save()
            
        
    if usuario.is_authenticated():
        return render_to_response('proyectos.html',{'equipos':equipos,'personal':personal, 'proyectos':proyectos}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    

@login_required(login_url='/ingresar')    
def nuevo_proyecto(request):
    usuario=request.user
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            miembros = Miembro.objects.filter(jefe=personal.id)
    if request.method == 'POST':
        formulario=ProyectoForm(request.POST)

        nombreProyecto = request.POST['nombreProyecto']
        fechaInicio = request.POST['fechaInicio']
        #if fechaInicio:
        #    fecha =  datetime.strptime(fechaInicio,"%d/%m/%Y").strftime("%Y-%m-%d")           
        descripcion = request.POST['descripcion']
        foco = request.POST['foco']
        equipo = request.POST.getlist('equipo')
        if not nombreProyecto or not fechaInicio or not descripcion or not equipo:
            #Datos obligatorios requeridos
            validacion=1
            return render_to_response('registroproyecto.html',{'validacion':validacion,'foco':foco,'descripcion':descripcion,'nombreProyecto':nombreProyecto,'fechaInicio':fechaInicio,'formulario':formulario, 'personal':personal, 'miembros':miembros}, context_instance=RequestContext(request))
        else:
            try:              
                existe = Proyecto.objects.get(nombreProyecto=nombreProyecto)
                #El proyecto ya existe
                validacion=2
                return render_to_response('registroproyecto.html',{'validacion':validacion,'foco':foco,'descripcion':descripcion,'nombreProyecto':nombreProyecto,'fechaInicio':fechaInicio,'formulario':formulario, 'personal':personal, 'miembros':miembros}, context_instance=RequestContext(request))
            except:
                #try:                        
                    p=formulario.save(commit=False)
                    p.historiasP = 0
                    p.spProyecto = 0
                    p.jefeProyecto = personal
                    p.save()
                #except:
                    #return HttpResponseRedirect('/passdiferentes')
            for dato in equipo:
                e = Equipo.objects.create(                       
                    proyecto = p,
                    miembro = Miembro.objects.get(id=dato),
                )
                e.save()                  
        return HttpResponseRedirect('/proyectos')

    else:
        formulario = ProyectoForm()
    return render_to_response('registroproyecto.html',{'formulario':formulario, 'personal':personal, 'miembros':miembros}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def editar_proyecto(request,id_proyecto):
    usuario=request.user
    proyecto=Proyecto.objects.get(id=id_proyecto)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            miembros = Miembro.objects.filter(jefe=personal.id)
    if request.method == 'POST':
        formulario=ProyectoForm(request.POST)

        nombreProyecto = request.POST['nombreProyecto']
        fechaInicio = request.POST['fechaInicio']
        #if fechaInicio:
        #    fecha =  datetime.strptime(fechaInicio,"%d/%m/%Y").strftime("%Y-%m-%d")           
        descripcion = request.POST['descripcion']
        foco = request.POST['foco']
        
        if not nombreProyecto or not fechaInicio or not descripcion:
            #Datos obligatorios requeridos
            validacion=1
            return render_to_response('editarproyecto.html',{'validacion':validacion, 'proyecto':proyecto,'formulario':formulario, 'personal':personal, 'miembros':miembros}, context_instance=RequestContext(request))
        else:
            try:              
                existe = Proyecto.objects.get(nombreProyecto=nombreProyecto)
                #Proyecto ya existe
                if existe.nombreProyecto != proyecto.nombreProyecto:
                    validacion=2
                    return render_to_response('editarproyecto.html',{'validacion':validacion, 'proyecto':proyecto,'formulario':formulario, 'personal':personal, 'miembros':miembros}, context_instance=RequestContext(request))
                else:
                    proyecto.nombreProyecto=nombreProyecto
                    proyecto.fechaInicio=fechaInicio
                    proyecto.descripcion=descripcion
                    proyecto.foco=foco
                    proyecto.save()
                    
                    return HttpResponseRedirect('/proyectos')
            except:
                #try:                        
                    proyecto.nombreProyecto=nombreProyecto
                    proyecto.fechaInicio=fechaInicio
                    proyecto.descripcion=descripcion
                    proyecto.foco=foco
                    proyecto.save()
                #except:
                    #return HttpResponseRedirect('/passdiferentes')
                             
        return HttpResponseRedirect('/proyectos')

    else:
        formulario = ProyectoForm()
    return render_to_response('editarproyecto.html',{'proyecto':proyecto,'formulario':formulario, 'personal':personal, 'miembros':miembros}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def eliminar_proyecto(request,id_proyecto):
    usuario=request.user
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyectos=Proyecto.objects.filter(jefeProyecto=personal.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyectos=Equipo.objects.filter(miembro=personal.id)
            
    proyecto=Proyecto.objects.get(id=id_proyecto)
    equipo=Equipo.objects.filter(proyecto_id=id_proyecto)
    proyecto.delete()
    equipo.delete()
          
    if usuario.is_authenticated():
        return render_to_response('proyectos.html',{'personal':personal, 'proyectos':proyectos}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def detalle_proyecto(request, id_proyecto):
    usuario=request.user
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(id=id_proyecto)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(id=id_proyecto)
          
    if usuario.is_authenticated():
        return render_to_response('detalleproyecto.html', {'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    
    
@login_required(login_url='/ingresar')    
def lista_historias(request, id_proyecto):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=id_proyecto)
    proyecto=Proyecto.objects.get(id=id_proyecto)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            historias=Historia.objects.filter(proyecto_id=id_proyecto)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            historias=Historia.objects.filter(proyecto_id=id_proyecto)
          
    if usuario.is_authenticated():
        return render_to_response('historias.html', {'personal':personal, 'historias':historias, 'proyecto':proyecto, 'equipo':equipo}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    

@login_required(login_url='/ingresar')    
def informe_productbacklog(request, id_proyecto):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipos=Equipo.objects.filter(proyecto=id_proyecto) 
    proyecto=Proyecto.objects.get(id=id_proyecto)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    
    
    sprints = Sprint.objects.filter(proyecto=id_proyecto)
    historiasTodas=Historia.objects.filter(sprint__in=sprints)
    
    
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            historias=Historia.objects.filter(proyecto_id=id_proyecto)
            tareas=Tarea.objects.filter(historia__in=historiasTodas)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            historias=Historia.objects.filter(proyecto_id=id_proyecto)
            tareas=Tarea.objects.filter(historia__in=historiasTodas)
          
    if usuario.is_authenticated():
        return render_to_response('informeProductBacklog.html', {'historiasTodas':historiasTodas,'sprints':sprints,'tareas':tareas,'equipos':equipos,'equipo':equipo,'personal':personal, 'historias':historias, 'proyecto':proyecto}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def nueva_historia(request, id_proyecto):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=id_proyecto)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=id_proyecto)
    if request.method == 'POST':
        formulario=HistoriaForm(request.POST)

        titulo = request.POST['titulo']
        descripcion = request.POST['descripcion']
        aceptacion = request.POST['aceptacion']
        #if fechaInicio:
        #    fecha =  datetime.strptime(fechaInicio,"%d/%m/%Y").strftime("%Y-%m-%d")           
        sp = request.POST['sp']
      
        if not titulo or not descripcion or not aceptacion:
            #titulo no puede estar vacio
            validacion=1
            return render_to_response('registrohistoria.html',{'equipo':equipo,'validacion':validacion,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
        else:
            try:              
                existe = Historia.objects.get(titulo=titulo)
                #La historia existe
                validacion=2
                return render_to_response('registrohistoria.html',{'equipo':equipo,'validacion':validacion,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
            except:
                #try:                        
                    p=formulario.save(commit=False)
                    p.estado = 0
                    p.proyecto = proyecto
                    p.creador = usuario
                    p.save()
                #except:
                    #return HttpResponseRedirect('/passdiferentes')
                    e = Proyecto.objects.get(pk=id_proyecto)
                    e.historiasP += 1
                    e.spProyecto += int(sp)
                    e.save()
        
        return HttpResponseRedirect(reverse('lista_historias',args=[id_proyecto]))            
    else:
        formulario = HistoriaForm()
    return render_to_response('registrohistoria.html',{'equipo':equipo,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def editar_historia(request, id_historia):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            historia=Historia.objects.get(id=id_historia)
            proyecto=Proyecto.objects.get(id=historia.proyecto.id)   
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            historia=Historia.objects.get(id=id_historia)
            proyecto=Proyecto.objects.get(id=historia.proyecto.id) 
    if request.method == 'POST':
        formulario=HistoriaForm(request.POST)

        titulo = request.POST['titulo']
        prioridad = request.POST['prioridad']
        descripcion = request.POST['descripcion']
        aceptacion = request.POST['aceptacion']
        #if fechaInicio:
        #    fecha =  datetime.strptime(fechaInicio,"%d/%m/%Y").strftime("%Y-%m-%d")           
        sp = request.POST['sp']
      
        if not titulo or not descripcion or not aceptacion:
            #datos obligatorios vacios
            validacion=1
            return render_to_response('editarhistoria.html',{'equipo':equipo,'validacion':validacion,'historia':historia,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
        else:             
            e = Proyecto.objects.get(pk=proyecto.id)
            e.spProyecto -= int(historia.sp)
            e.spProyecto += int(sp)
            e.save()
        #try:              
        
            historia.titulo = titulo
            historia.prioridad=prioridad
            historia.descripcion=descripcion
            historia.aceptacion=aceptacion
            historia.sp=int(sp)
            historia.estado = 0
            historia.proyecto = proyecto
            historia.creador = usuario
            historia.save()
        #except:
            #return HttpResponseRedirect('/passdiferentes')
                        
            
            return HttpResponseRedirect(reverse('lista_historias',args=[proyecto.id]))            

    else:
        formulario = HistoriaForm()
    return render_to_response('editarhistoria.html',{'equipo':equipo,'historia':historia,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def eliminar_historia(request, id_historia):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id)
    historia=Historia.objects.get(id=id_historia)
    proyecto=Proyecto.objects.get(id=historia.proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            historias=Historia.objects.filter(proyecto_id=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            historias=Historia.objects.filter(proyecto_id=proyecto.id)
        
        e = Proyecto.objects.get(pk=proyecto.id)
        e.historiasP -= 1
        e.spProyecto -= int(historia.sp)
        e.save()
                       
        historia.delete()
          
    if usuario.is_authenticated():
        return render_to_response('historias.html', {'equipo':equipo,'personal':personal, 'historias':historias, 'proyecto':proyecto}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    


@login_required(login_url='/ingresar')    
def detalle_historia(request, id_historia):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    historia=Historia.objects.get(id=id_historia)
    proyecto=Proyecto.objects.get(id=historia.proyecto.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia_id=id_historia)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia_id=id_historia)
          
    if usuario.is_authenticated():
        return render_to_response('detallehistoria.html', {'equipo':equipo,'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historia':historia}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def nueva_tarea(request, id_proyecto, id_historia):
    usuario=request.user
    historia=Historia.objects.get(pk=id_historia)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=id_proyecto)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=id_proyecto)
    
    if request.method == 'POST':
        formulario=TareaForm(request.POST)

        resumen = request.POST['resumen']           
        descripcion = request.POST['descripcion']
        esfuerzo = request.POST['esfuerzo']
      
        if not resumen or not esfuerzo or not descripcion:
            #Rellenar campos obligatorios
            validacion=1
            return render_to_response('registrotarea.html',{'validacion':validacion,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))

        else:
            try: 
                validate_integer(esfuerzo)                    
                p=formulario.save(commit=False)
                p.estado = 0
                p.historia = historia
                p.proyecto = proyecto
                p.esfuerzo = esfuerzo
                p.creador = usuario
                p.save()   
            except:
                #El esfuerzo tiene que ser un numero entero
                validacion=2
                return render_to_response('registrotarea.html',{'validacion':validacion,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))                 
        
        return HttpResponseRedirect(reverse('detalle_historia',args=[id_historia]))            

    else:
        formulario = TareaForm()
    return render_to_response('registrotarea.html',{'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def editar_tarea(request, id_tarea):
    usuario=request.user
    tarea=Tarea.objects.get(pk=id_tarea)
    historia=Historia.objects.get(pk=tarea.historia.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=historia.proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=historia.proyecto.id)
    
    if request.method == 'POST':
        formulario=TareaForm(request.POST)

        resumen = request.POST['resumen']           
        descripcion = request.POST['descripcion']
        esfuerzo = request.POST['esfuerzo']
      
        if not resumen or not esfuerzo or not descripcion:
            #Rellenar campos obligatorios
            validacion=1
            return render_to_response('editartarea.html',{'validacion':validacion,'tarea':tarea, 'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
        else:   
            try: 
                validate_integer(esfuerzo)                    
                tarea.resumen = resumen
                tarea.descripcion = descripcion                 
                tarea.estado = 0
                tarea.esfuerzo = esfuerzo
                tarea.creador = usuario
                tarea.save()   
            except:
                #El esfuerzo tiene que ser un numero entero
                validacion=2
                return render_to_response('editartarea.html',{'validacion':validacion,'tarea':tarea, 'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
                      
        return HttpResponseRedirect(reverse('detalle_historia',args=[historia.id]))            

    else:
        formulario = TareaForm()
    return render_to_response('editartarea.html',{'tarea':tarea, 'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def eliminar_tarea(request, id_tarea):
    usuario=request.user
    tarea=Tarea.objects.get(pk=id_tarea)
    historia=Historia.objects.get(pk=tarea.historia.id)
    proyecto=Proyecto.objects.get(pk=historia.proyecto.id)
    
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia_id=historia.id)
            miembro=Miembro.objects.get(usuario=usuario.id)
            equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia_id=historia.id)
            equipo=Equipo.objects.filter(miembro_id=personal.id).get(proyecto_id=proyecto.id)
    
    tarea.delete()
          
    if usuario.is_authenticated():
        return render_to_response('detallehistoria.html', {'equipo':equipo, 'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historia':historia}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def lista_sprints(request, id_proyecto):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    proyecto=Proyecto.objects.get(id=id_proyecto)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
        
        horasEstimadas=0
        horasTerminadas=0
        velocidadOb=0
        velocidadReal=0
        for sprint in sprints: 
            historias = Historia.objects.filter(sprint_id=sprint.id)
            tareas = Tarea.objects.filter(historia__in=historias)
            tareasTerminadas = Tarea.objects.filter(historia__in=historias).filter(estado=2)
            for historia in historias:
                t=Tarea.objects.filter(historia=historia)
                ts = Tarea.objects.filter(historia=historia).filter(estado=2)
                if (len(t) == len(ts)) and len(t) != 0 and len(ts) != 0:
                    velocidadReal += historia.sp
                velocidadOb += historia.sp
            for tarea in tareasTerminadas:
                horasTerminadas += tarea.esfuerzo
            for tarea in tareas:
                horasEstimadas += tarea.esfuerzo
            s = Sprint.objects.get(id=sprint.id)      
            s.nTareas = len(tareas)
            s.velocidadOb = velocidadOb
            s.velocidadReal = velocidadReal
            s.hEstimadas = horasEstimadas
            s.hPendientes = horasEstimadas-horasTerminadas
            s.save()
            horasEstimadas=0
            horasTerminadas=0
            velocidadOb=0
            velocidadReal=0
        
        
    if usuario.is_authenticated():
        return render_to_response('sprints.html', {'equipo':equipo,'personal':personal, 'sprints':sprints, 'proyecto':proyecto}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def nuevo_sprint(request, id_proyecto):
    dedicaciones=[]
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            proyecto=Proyecto.objects.get(id=id_proyecto)
            personal=Personal.objects.get(usuario=usuario.id)
            equipo = Equipo.objects.filter(proyecto_id=id_proyecto).order_by('id')
            historias=Historia.objects.filter(proyecto_id=id_proyecto).filter(sprint_id=None)
        else:
            proyecto=Proyecto.objects.get(id=id_proyecto)
            personal=Miembro.objects.get(usuario=usuario.id)
            equipo = Equipo.objects.filter(proyecto_id=id_proyecto).order_by('id')
            historias=Historia.objects.filter(proyecto_id=id_proyecto).filter(sprint_id=None)

    if request.method == 'POST':
        formulario=SprintForm(request.POST)

        nombreSprint = request.POST['nombre']
        fechaInicio = request.POST['fechaInicio']
        objetivo = request.POST['Objetivo']
        duracion = request.POST['duracion']
        fechaRevision = request.POST['fechaRevision']

        historiasSprint = request.POST.getlist('historiasSprint')
        
        
        for dato in equipo:
            dedicaciones.append(request.POST['foco_'+str(dato.id)])  

        #if fechaInicio:
        #    fecha =  datetime.strptime(fechaInicio,"%d/%m/%Y").strftime("%Y-%m-%d")           
        
        if not nombreSprint or not fechaInicio or not objetivo or not historiasSprint or not fechaRevision:
            if fechaInicio:
                print "dentro de fechainicio"
                fechaInicio = datetime.strptime(fechaInicio,'%Y-%m-%d') 
            if fechaRevision:
                fechaRevision = datetime.strptime(fechaRevision,'%Y-%m-%d') 
                print "dentro de fecharevision"
            #rellenar campos obligatorios
            validacion=1
            return render_to_response('registrosprint.html',{'equipo':equipo,'duracion':duracion,'fechaRevision':fechaRevision,'objetivo':objetivo,'fechaInicio':fechaInicio,'nombreSprint':nombreSprint,'validacion':validacion,'formulario':formulario, 'personal':personal, 'equipo':equipo, 'historias':historias, 'proyecto':proyecto}, context_instance=RequestContext(request))
        else:
            if fechaInicio:
                fechaInicio = datetime.strptime(fechaInicio,'%Y-%m-%d') 
            if fechaRevision:
                fechaRevision = datetime.strptime(fechaRevision,'%Y-%m-%d') 
            try:              
                existe = Sprint.objects.get(nombre=nombreSprint)
                fechaInicio = datetime.strptime(fechaInicio,'%Y-%m-%d')
                fechaRevision = datetime.strptime(fechaRevision,'%Y-%m-%d')  
                #el nombre del sprint existe
                validacion=2
                return render_to_response('registrosprint.html',{'equipo':equipo,'duracion':duracion,'fechaRevision':fechaRevision,'objetivo':objetivo,'fechaInicio':fechaInicio,'nombreSprint':nombreSprint,'validacion':validacion,'formulario':formulario, 'personal':personal, 'equipo':equipo, 'historias':historias, 'proyecto':proyecto}, context_instance=RequestContext(request))
            except:
                #try:   
                    
                    fechaFin = fechaInicio + timedelta(days=((7*(int(duracion)))))                   
                    p=formulario.save(commit=False)
                    p.fechaFin = fechaFin
                    p.estado = 1
                    p.nTareas = 0
                    p.hEstimadas = 0
                    p.hPendientes = 0
                    p.velocidadObj = 0
                    p.velocidadReal = 0
                    p.proyecto = proyecto
                    p.save()
                #except:
                    #return HttpResponseRedirect('/passdiferentes')
                    
                    #Agrego al equipo la dedicacion y el sprint
                    for i in range(len(equipo)):
                        equipo[i].dedicacion = dedicaciones[i]
                        equipo[i].sprint = p
                        equipo[i].save() 
                    
                    for dato in historiasSprint: 
                        historia = Historia.objects.get(id=dato)   
                        print historia        
                        historia.sprint = p
                        historia.save()
                        
                              
        return HttpResponseRedirect(reverse('lista_sprints',args=[id_proyecto]))

    else:
        formulario = SprintForm()
    return render_to_response('registrosprint.html',{'equipo':equipo,'formulario':formulario, 'personal':personal, 'equipo':equipo, 'historias':historias, 'proyecto':proyecto}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def editar_sprint(request, id_sprint):
    dedicaciones=[]
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id)
    sprint= Sprint.objects.get(id=id_sprint)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
            personal=Personal.objects.get(usuario=usuario.id)
            equipo = Equipo.objects.filter(proyecto_id=sprint.proyecto.id).order_by('id')
            historias=Historia.objects.filter(proyecto_id=sprint.proyecto.id).filter(sprint_id=None)
            historiasSprint=Historia.objects.filter(sprint_id=id_sprint)
        else:
            proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
            personal=Miembro.objects.get(usuario=usuario.id)
            equipo = Equipo.objects.filter(proyecto_id=sprint.proyecto.id).order_by('id')
            historias=Historia.objects.filter(proyecto_id=sprint.proyecto.id).filter(sprint_id=None)
            historiasSprint=Historia.objects.filter(sprint_id=id_sprint)

    if request.method == 'POST':
        formulario=SprintForm(request.POST)
        
        nombreSprint = request.POST['nombre']
        fechaInicio = request.POST['fechaInicio']
        objetivo = request.POST['Objetivo']
        duracion = request.POST['duracion']
        fechaRevision = request.POST['fechaRevision']

        historiasSelectSprint = request.POST.getlist('historiasSprint')
        
        print duracion
        for dato in equipo:
            dedicaciones.append(request.POST['foco_'+str(dato.id)])  

        #if fechaInicio:
        #    fecha =  datetime.strptime(fechaInicio,"%d/%m/%Y").strftime("%Y-%m-%d")           
        
        
        
        if not nombreSprint or not fechaInicio or not objetivo or not historiasSelectSprint or not fechaRevision:

            if fechaInicio:
                fechaInicio = datetime.strptime(fechaInicio,'%Y-%m-%d') 
            if fechaRevision:
                fechaRevision = datetime.strptime(fechaRevision,'%Y-%m-%d') 
            #rellenar campos obligatorios
            print "Estoy dentro"
            validacion=1
            return render_to_response('editarsprint.html',{'equipo':equipo,'validacion':validacion,'historiasSprint':historiasSprint,'sprint':sprint,'formulario':formulario, 'personal':personal, 'equipo':equipo, 'historias':historias, 'proyecto':proyecto}, context_instance=RequestContext(request))
            
        else:  
            try:    

                existe = Sprint.objects.get(nombre=nombreSprint)
                fechaInicio = datetime.strptime(fechaInicio,'%Y-%m-%d')
                fechaRevision = datetime.strptime(fechaRevision,'%Y-%m-%d')     
     
                if existe.nombre != sprint.nombre:
                    #el nombre del sprint existe
                    validacion=2
                    return render_to_response('editarsprint.html',{'equipo':equipo,'validacion':validacion,'historiasSprint':historiasSprint,'sprint':sprint,'formulario':formulario, 'personal':personal, 'equipo':equipo, 'historias':historias, 'proyecto':proyecto}, context_instance=RequestContext(request))
                else:                         
                    fechaFin = fechaInicio + timedelta(days=((7*(int(duracion))))) 
                    sprint.nombre=nombreSprint
                    sprint.fechaInicio=fechaInicio
                    sprint.fechaFin=fechaFin
                    sprint.fechaRevision=fechaRevision
                    sprint.Objetivo=objetivo
                    sprint.duracion=duracion
                    sprint.estado = 1
                    sprint.save()
                    
                    #Agrego al equipo la dedicacion y el sprint
                    for i in range(len(equipo)):
                        equipo[i].dedicacion = dedicaciones[i]
                        equipo[i].sprint = sprint
                        equipo[i].save() 
                    
                    for dato in historiasSelectSprint: 
                        historia = Historia.objects.get(id=dato)   
                        print historia        
                        historia.sprint = sprint
                        historia.save()
                        
                    sprintBorrar=historiasSprint.exclude(id__in=historiasSelectSprint)
                    
                    for dato in sprintBorrar: 
                        historia = Historia.objects.get(id=dato.id)        
                        historia.sprint = None
                        historia.save()
                    
                    return HttpResponseRedirect(reverse('lista_sprints',args=[sprint.proyecto.id]))

            except:        
                #try:  
                    fechaInicio = datetime.strptime(fechaInicio,'%Y-%m-%d')
                    fechaRevision = datetime.strptime(fechaRevision,'%Y-%m-%d')                          
                    fechaFin = fechaInicio + timedelta(days=((7*(int(duracion))))) 
                    print fechaFin
                    sprint.nombre=nombreSprint
                    sprint.fechaInicio=fechaInicio
                    sprint.fechaFin=fechaFin
                    sprint.fechaRevision=fechaRevision
                    sprint.Objetivo=objetivo
                    sprint.duracion=duracion
                    sprint.estado = 1
                    sprint.save()
                #except:
                    #return HttpResponseRedirect('/passdiferentes')
                    
                    #Agrego al equipo la dedicacion y el sprint
                    for i in range(len(equipo)):
                        equipo[i].dedicacion = dedicaciones[i]
                        equipo[i].sprint = sprint
                        equipo[i].save() 
                    
                    for dato in historiasSelectSprint: 
                        historia = Historia.objects.get(id=dato)   
                        print historia        
                        historia.sprint = sprint
                        historia.save()
                        
                    sprintBorrar=historiasSprint.exclude(id__in=historiasSelectSprint)
                    
                    for dato in sprintBorrar: 
                        historia = Historia.objects.get(id=dato.id)        
                        historia.sprint = None
                        historia.save()

                    
        return HttpResponseRedirect(reverse('lista_sprints',args=[sprint.proyecto.id]))

    else:
        formulario = SprintForm()
    return render_to_response('editarsprint.html',{'equipo':equipo,'historiasSprint':historiasSprint,'sprint':sprint,'formulario':formulario, 'personal':personal, 'equipo':equipo, 'historias':historias, 'proyecto':proyecto}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def cerrar_sprint(request, id_sprint):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id)
    sprint= Sprint.objects.get(id=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=sprint.proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=sprint.proyecto.id)
            
    sprint.estado = 0
    sprint.save()
          
    if usuario.is_authenticated():
        return render_to_response('sprints.html', {'equipo':equipo,'personal':personal, 'sprints':sprints, 'proyecto':proyecto}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))




@login_required(login_url='/ingresar')    
def detalle_sprint(request, id_sprint):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.get(miembro_id=miembro.id)
    sprint = Sprint.objects.get(id=id_sprint)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(id=sprint.proyecto_id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(id=sprint.proyecto_id)
          
    if usuario.is_authenticated():
        return render_to_response('detallesprint.html', {'equipo':equipo,'personal':personal, 'proyecto':proyecto, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    
    
@login_required(login_url='/ingresar')    
def calendario(request, id_proyecto):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(id=id_proyecto)
            sprints=Sprint.objects.filter(proyecto=id_proyecto)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(id=id_proyecto)
            sprints=Sprint.objects.filter(proyecto=id_proyecto)
    
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
          
    if usuario.is_authenticated():
        return render_to_response('calendario.html', {'equipo':equipo,'personal':personal, 'proyecto':proyecto, 'sprints':sprints}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    
    

@login_required(login_url='/ingresar')    
def lista_sprintbacklog(request, id_sprint):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            
    formulario = TareaForm()
          
    if usuario.is_authenticated():
        return render_to_response('sprintbacklog.html', {'equipo':equipo,'formulario':formulario, 'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historias':historias, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))

@login_required(login_url='/ingresar')    
def nueva_tarea_modal(request, id_proyecto, id_historia):
    print id_historia
    usuario=request.user
    historia=Historia.objects.get(pk=id_historia)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=id_proyecto)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=id_proyecto)
    
    if request.method == 'POST':
        formulario=TareaForm(request.POST)
        
        resumen = request.POST['resumen']           
        descripcion = request.POST['descripcion']
        esfuerzo = request.POST['esfuerzo']
      
        if not resumen or not esfuerzo or not descripcion:
            #Rellenar campos obligatorios
            validacion=1
            return render_to_response('registrotarea.html',{'validacion':validacion,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
        else:   
            try: 
                validate_integer(esfuerzo)                    
                p=formulario.save(commit=False)
                p.estado = 0
                p.historia = historia
                p.proyecto = proyecto
                p.esfuerzo = esfuerzo
                p.creador = usuario
                p.save()   
            except:
                #El esfuerzo tiene que ser un numero entero
                validacion=2
                return render_to_response('registrotarea.html',{'validacion':validacion,'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))                   
        
        return HttpResponseRedirect(reverse('lista_sprintbacklog',args=[historia.sprint_id]))            
        
    else:
        formulario = TareaForm()
    return render_to_response('registrotarea.html',{'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def editar_tarea_modal(request, id_tarea):
    usuario=request.user
    tarea= Tarea.objects.get(pk=id_tarea)
    historia=Historia.objects.get(pk=tarea.historia.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=tarea.proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=tarea.proyecto.id)
    
    if request.method == 'POST':
        formulario=TareaForm(request.POST)
        if formulario.is_valid():
            resumen = request.POST['resumen']           
            descripcion = request.POST['descripcion']
            esfuerzo = request.POST['esfuerzo']
            
            
            if not resumen or not esfuerzo or not descripcion:
                #Rellenar campos obligatorios
                validacion=1
                return render_to_response('editartarea.html',{'validacion':validacion,'tarea':tarea, 'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
            else:   
                try: 
                    validate_integer(esfuerzo)                    
                    tarea.resumen = resumen
                    tarea.descripcion = descripcion                 
                    tarea.estado = 0
                    tarea.esfuerzo = esfuerzo
                    tarea.creador = usuario
                    tarea.save()   
                except:
                    #El esfuerzo tiene que ser un numero entero
                    validacion=2
                    return render_to_response('editartarea.html',{'validacion':validacion,'tarea':tarea, 'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))
                          
            return HttpResponseRedirect(reverse('lista_sprintbacklog',args=[historia.sprint_id])) 
            
            

    else:
        formulario = TareaForm()
    return render_to_response('registrotarea.html',{'formulario':formulario, 'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')    
def eliminar_tarea_modal(request, id_tarea):
    usuario=request.user
    tarea= Tarea.objects.get(pk=id_tarea)
    historia=Historia.objects.get(pk=tarea.historia.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=tarea.proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            proyecto=Proyecto.objects.get(pk=tarea.proyecto.id)
                           
        tarea.delete()                   
            
        return HttpResponseRedirect(reverse('lista_sprintbacklog',args=[historia.sprint_id]))            

    return render_to_response('registrotarea.html',{'personal':personal, 'proyecto':proyecto}, context_instance=RequestContext(request))



@login_required(login_url='/ingresar')    
def ver_muro(request, id_sprint):
    fechaHoy=date.today()
    fechaHoy.strftime("%y-%m-%d")
    usuario=request.user
    sprint = Sprint.objects.get(id=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    historias=Historia.objects.filter(sprint=id_sprint)
    
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
          
    if usuario.is_authenticated():
        return render_to_response('muro.html', {'equipo':equipo,'fechaHoy':fechaHoy,'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historias':historias, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    

@login_required(login_url='/ingresar')    
def asignar_tarea(request, id_sprint, id_tarea):
    usuario=request.user
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
    tarea=Tarea.objects.get(id=id_tarea)
    tarea.realizador = personaEquipo[0]
    tarea.save()
          
    if usuario.is_authenticated():
        return HttpResponseRedirect(reverse('lista_sprintbacklog',args=[id_sprint]))  
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    
@login_required(login_url='/ingresar')    
def quitarAsignar_tarea(request, id_sprint, id_tarea):
    usuario=request.user
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
    tarea=Tarea.objects.get(id=id_tarea)
    tarea.realizador = None
    tarea.save()
          
    if usuario.is_authenticated():
        return HttpResponseRedirect(reverse('lista_sprintbacklog',args=[id_sprint]))  
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))



@login_required(login_url='/ingresar')    
def sprints_poker(request, id_proyecto):
    usuario=request.user
    proyecto=Proyecto.objects.get(id=id_proyecto)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
    if request.method == 'POST':
        formulario=SelectSprintForm(request.POST)
        if formulario.is_valid():
            id_sprint = request.POST['sprint']
            sprint = Sprint.objects.get(id=id_sprint)           
            historias = Historia.objects.filter(sprint = id_sprint)
            tareas=Tarea.objects.filter(historia__in=historias)
            
                       
            
            return HttpResponseRedirect(reverse('planning_poker',args=[id_proyecto,sprint.id]))
        else:
            return HttpResponseRedirect('/formularioNoValido')
    else:
        formulario = SelectSprintForm()
    
          
    if usuario.is_authenticated():
        return render_to_response('sprintpoker.html', {'personaEquipo':personaEquipo[0],'personal':personal, 'sprints':sprints, 'proyecto':proyecto, 'formulario':formulario}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))    


@login_required(login_url='/ingresar')    
def planning_poker(request,id_proyecto, id_sprint):
    usuario=request.user
    proyecto=Proyecto.objects.get(id=id_proyecto)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        
        sprint = Sprint.objects.get(id=id_sprint)                     
        historias = Historia.objects.filter(sprint = id_sprint)
        tareas=Tarea.objects.filter(historia__in=historias)
        
        historiasVotadas=Poker.objects.filter(jugador_id=personaEquipo[0].id)
        resultadoPoker=Poker.objects.filter(sprint_id=id_sprint)
        
        if request.method == 'POST':
            formulario=SelectSprintForm(request.POST)
            if formulario.is_valid():
                id_sprint = request.POST['sprint']
                sprint = Sprint.objects.get(id=id_sprint)           
                historias = Historia.objects.filter(sprint = id_sprint)
                tareas=Tarea.objects.filter(historia__in=historias)
             
                return HttpResponseRedirect(reverse('planning_poker',args=[id_proyecto,sprint.id]))
            else:
                return HttpResponseRedirect('/formularioNoValido')
        else:
            formulario = SelectSprintForm()
    
          
    if usuario.is_authenticated():
        return render_to_response('poker.html', {'resultadoPoker':resultadoPoker,'historiasVotadas':historiasVotadas,'personaEquipo':personaEquipo[0],'personal':personal, 'sprints':sprints, 'valueSprint':sprint, 'historias':historias, 'tareas':tareas, 'proyecto':proyecto, 'formulario':formulario}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))    
    
    
    
@login_required(login_url='/ingresar')    
def votar_poker(request, id_proyecto, id_sprint, id_historia, voto):
    usuario=request.user
    proyecto=Proyecto.objects.get(id=id_proyecto)
    sprint=Sprint.objects.get(id=id_sprint)
    historia=Historia.objects.get(id=id_historia)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
            
        try:              
            existe = Poker.objects.get(jugador=personaEquipo[0],proyecto_id=id_proyecto,sprint_id=id_sprint,historia_id=id_historia)
            existe.votado = 1
            existe.spVotado = voto
            existe.save()
        except:                     
            v = Poker.objects.create(                       
                proyecto = proyecto,
                sprint = sprint,
                historia = historia,
                votado = 1,
                spVotado = voto,
                jugador = personaEquipo[0],
            )
            v.save()  
    
          
    if usuario.is_authenticated():
         return HttpResponseRedirect(reverse('planning_poker',args=[id_proyecto,id_sprint])) 
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request)) 
    

@login_required(login_url='/ingresar')    
def elegir_estimacion(request, id_proyecto, id_sprint, id_historia, voto):
    usuario=request.user
    proyecto=Proyecto.objects.get(id=id_proyecto)
    sprint=Sprint.objects.get(id=id_sprint)
    historia=Historia.objects.get(id=id_historia)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
        
        e = Proyecto.objects.get(pk=proyecto.id)
        e.spProyecto -= int(historia.sp)
        e.spProyecto += int(voto)
        e.save()
                       
        historia.sp = voto
        historia.save()
 
    
          
    if usuario.is_authenticated():
         return HttpResponseRedirect(reverse('planning_poker',args=[id_proyecto,id_sprint])) 
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request)) 
    
    
    
@login_required(login_url='/ingresar')    
def reiniciar_estimacion(request, id_proyecto, id_sprint, id_historia):
    usuario=request.user
    proyecto=Proyecto.objects.get(id=id_proyecto)
    sprint=Sprint.objects.get(id=id_sprint)
    historia=Historia.objects.get(id=id_historia)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            sprints=Sprint.objects.filter(proyecto_id=id_proyecto)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
                       
            
        existe = Poker.objects.filter(historia=historia)
        existe.delete()                  
    
          
    if usuario.is_authenticated():
         return HttpResponseRedirect(reverse('planning_poker',args=[id_proyecto,id_sprint])) 
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request)) 
    
    
@login_required(login_url='/ingresar')    
def ver_graficas(request, id_sprint):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            
    dias = sprint.fechaFin - sprint.fechaInicio
    listaEtiquetaGrafica=[]
    sumaEsfuerzo=[]   
    suma=0
    datosTareasGrafica=[]
    esfuerzoIdeal=[]
    
    for tarea in tareas:
        suma=suma+tarea.esfuerzo
        datosTareasGrafica.append(tarea.esfuerzo)
    
    media=suma/dias.days
    valor=suma+media
    
    for i in range(dias.days):
        fecha=sprint.fechaInicio + timedelta(days=i)       
        for tarea in tareas:
            if (tarea.fechaEstado==fecha) and (tarea.estado == 2):
                print "tarea terminada"
                suma=suma-tarea.esfuerzo
                print suma
        sumaEsfuerzo.append(str(suma))
                
        valor=valor-media
        esfuerzoIdeal.append(str(valor))
        
        listaEtiquetaGrafica.append(fecha.strftime("%d %b"))
    #EtiquetaGraficas="'"+"', '".join(EtiquetaGraficas)+"'"
    
    
    sumaEsfuerzo=",".join(sumaEsfuerzo)
    esfuerzoIdeal=",".join(esfuerzoIdeal)
    
    print esfuerzoIdeal
        
    if usuario.is_authenticated():
        return render_to_response('graficas.html', {'equipo':equipo,'esfuerzoIdeal':esfuerzoIdeal,'esfuerzo':sumaEsfuerzo,'etiquetas':listaEtiquetaGrafica,'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historias':historias, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    
    
@login_required(login_url='/ingresar')    
def informe_graficas(request, id_sprint):
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Personal.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            
    dias = sprint.fechaFin - sprint.fechaInicio
    listaEtiquetaGrafica=[]
    sumaEsfuerzo=[]   
    suma=0
    datosTareasGrafica=[]
    esfuerzoIdeal=[]
    
    for tarea in tareas:
        suma=suma+tarea.esfuerzo
        datosTareasGrafica.append(tarea.esfuerzo)
    
    media=suma/dias.days
    valor=suma+media
    
    for i in range(dias.days):
        fecha=sprint.fechaInicio + timedelta(days=i)       
        for tarea in tareas:
            if (tarea.fechaEstado==fecha) and (tarea.estado == 2):
                print "tarea terminada"
                suma=suma-tarea.esfuerzo
                print suma
        sumaEsfuerzo.append(str(suma))
                
        valor=valor-media
        esfuerzoIdeal.append(str(valor))
        
        listaEtiquetaGrafica.append(fecha.strftime("%d %b"))
    #EtiquetaGraficas="'"+"', '".join(EtiquetaGraficas)+"'"
    
    
    sumaEsfuerzo=",".join(sumaEsfuerzo)
    esfuerzoIdeal=",".join(esfuerzoIdeal)
    
    print esfuerzoIdeal
    
          
    if usuario.is_authenticated():
        return render_to_response('informegraficas.html', {'equipo':equipo,'esfuerzoIdeal':esfuerzoIdeal,'esfuerzo':sumaEsfuerzo,'etiquetas':listaEtiquetaGrafica,'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historias':historias, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))



@login_required(login_url='/ingresar')    
def borrar_comentario(request, id_comentario):
    usuario=request.user
    comentario=ComentarioReuniones.objects.get(id=id_comentario) 

    if comentario.reunion == 1:
        comentario.delete()
        return HttpResponseRedirect(reverse('ver_sprintplanning',args=[comentario.sprint.id]))
    if comentario.reunion == 2:
        comentario.delete()
        return HttpResponseRedirect(reverse('ver_sprintreview',args=[comentario.sprint.id]))
    if comentario.reunion == 3:
        comentario.delete()
        return HttpResponseRedirect(reverse('ver_sprintretrospective',args=[comentario.sprint.id]))
    if comentario.reunion == 4:
        comentario.delete()
        return HttpResponseRedirect(reverse('ver_dailyscrum',args=[comentario.sprint.id]))
    
    
        
    



@login_required(login_url='/ingresar')    
def ver_sprintplanning(request, id_sprint):
    hoy=date.today()
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    comentarios=ComentarioReuniones.objects.filter(reunion=1).filter(sprint_id=sprint.id).order_by('-fechahora')
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
    fechasDiferentes=comentarios.values_list('fecha',flat=True).order_by('-fecha').distinct()
    print fechasDiferentes
    
    
    if request.method == 'POST':
        formulario=ComentarioReunionesForm(request.POST)
        if formulario.is_valid():
            mensaje = request.POST['mensaje']
            
            c = ComentarioReuniones.objects.create(                       
                proyecto = proyecto,
                sprint = sprint,
                persona = personaEquipo[0],
                reunion = 1,
                mensaje = mensaje,
            )
            c.save()
            
            return HttpResponseRedirect(reverse('ver_sprintplanning',args=[sprint.id]))
        else:
            return HttpResponseRedirect('/formularioNoValido')
    else:
        formulario = SelectSprintForm()
    
          
    if usuario.is_authenticated():
        return render_to_response('sprintplanning.html', {'equipo':equipo,'hoy':hoy,'fechasDiferentes':fechasDiferentes,'comentarios':comentarios,'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historias':historias, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    

@login_required(login_url='/ingresar')    
def ver_sprintreview(request, id_sprint):
    hoy=date.today()
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    comentarios=ComentarioReuniones.objects.filter(reunion=2).filter(sprint_id=sprint.id).order_by('-fechahora')
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
    fechasDiferentes=comentarios.values_list('fecha',flat=True).order_by('-fecha').distinct()
    print fechasDiferentes
    
    
    if request.method == 'POST':
        formulario=ComentarioReunionesForm(request.POST)
        if formulario.is_valid():
            mensaje = request.POST['mensaje']
            
            c = ComentarioReuniones.objects.create(                       
                proyecto = proyecto,
                sprint = sprint,
                persona = personaEquipo[0],
                reunion = 2,
                mensaje = mensaje,
            )
            c.save()
            
            return HttpResponseRedirect(reverse('ver_sprintreview',args=[sprint.id]))
        else:
            return HttpResponseRedirect('/formularioNoValido')
    else:
        formulario = SelectSprintForm()
    
          
    if usuario.is_authenticated():
        return render_to_response('sprintreview.html', {'equipo':equipo,'hoy':hoy,'fechasDiferentes':fechasDiferentes,'comentarios':comentarios,'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historias':historias, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    
    
@login_required(login_url='/ingresar')    
def ver_sprintretrospective(request, id_sprint):
    hoy=date.today()
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    comentarios=ComentarioReuniones.objects.filter(reunion=3).filter(sprint_id=sprint.id).order_by('-fechahora')
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
    fechasDiferentes=comentarios.values_list('fecha',flat=True).order_by('-fecha').distinct()
    print fechasDiferentes
    
    
    if request.method == 'POST':
        formulario=ComentarioReunionesForm(request.POST)
        if formulario.is_valid():
            mensaje = request.POST['mensaje']
            
            c = ComentarioReuniones.objects.create(                       
                proyecto = proyecto,
                sprint = sprint,
                persona = personaEquipo[0],
                reunion = 3,
                mensaje = mensaje,
            )
            c.save()
            
            return HttpResponseRedirect(reverse('ver_sprintretrospective',args=[sprint.id]))
        else:
            return HttpResponseRedirect('/formularioNoValido')
    else:
        formulario = SelectSprintForm()
    
          
    if usuario.is_authenticated():
        return render_to_response('sprintretrospective.html', {'equipo':equipo,'hoy':hoy,'fechasDiferentes':fechasDiferentes,'comentarios':comentarios,'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historias':historias, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    

@login_required(login_url='/ingresar')    
def ver_dailyscrum(request, id_sprint):
    hoy=date.today()
    usuario=request.user
    miembro=Miembro.objects.get(usuario_id=usuario.id)
    sprint = Sprint.objects.get(id=id_sprint)
    historias=Historia.objects.filter(sprint=id_sprint)
    proyecto=Proyecto.objects.get(id=sprint.proyecto.id)
    equipo=Equipo.objects.filter(miembro_id=miembro.id).get(proyecto_id=proyecto.id)
    comentarios=ComentarioReuniones.objects.filter(reunion=4).filter(sprint_id=sprint.id).order_by('-fechahora')
    if usuario.is_authenticated():
        if usuario.is_superuser:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
        else:
            personal=Miembro.objects.get(usuario=usuario.id)
            tareas=Tarea.objects.filter(historia__in=historias)
            personaEquipo=Equipo.objects.filter(miembro=personal.id).filter(proyecto=proyecto.id)
            
    fechasDiferentes=comentarios.values_list('fecha',flat=True).order_by('-fecha').distinct()
    print fechasDiferentes
    
    
    if request.method == 'POST':
        formulario=ComentarioReunionesForm(request.POST)
        if formulario.is_valid():
            mensaje = request.POST['mensaje']
            
            c = ComentarioReuniones.objects.create(                       
                proyecto = proyecto,
                sprint = sprint,
                persona = personaEquipo[0],
                reunion = 4,
                mensaje = mensaje,
            )
            c.save()
            
            return HttpResponseRedirect(reverse('ver_dailyscrum',args=[sprint.id]))
        else:
            return HttpResponseRedirect('/formularioNoValido')
    else:
        formulario = SelectSprintForm()
    
          
    if usuario.is_authenticated():
        return render_to_response('dailyscrum.html', {'equipo':equipo,'hoy':hoy,'fechasDiferentes':fechasDiferentes,'comentarios':comentarios,'personal':personal, 'tareas':tareas, 'proyecto':proyecto, 'historias':historias, 'sprint':sprint}, context_instance=RequestContext(request))
    else:
        return render_to_response('inicio.html', context_instance=RequestContext(request))
    
    