import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from .models import OrdenReparacion, ClienteFacturacion, Repuesto # <-- Importamos Repuesto

def dashboard(request):
    query = request.GET.get('q', '')
    
    ordenes_pendientes = OrdenReparacion.objects.exclude(
        estado__in=['ENTREGADO', 'RECHAZADO']
    ).order_by('-fecha_ingreso')
    
    ordenes_entregadas = OrdenReparacion.objects.filter(
        estado='ENTREGADO'
    ).order_by('-fecha_entrega')
    
    clientes_facturacion = ClienteFacturacion.objects.all().order_by('-fecha_registro')
    
    # NUEVO: Traemos el inventario de repuestos ordenado por nombre
    repuestos = Repuesto.objects.all().order_by('nombre')
    
    if query:
        ordenes_pendientes = ordenes_pendientes.filter(
            Q(nombre_cliente__icontains=query) |
            Q(telefono_cliente__icontains=query) |
            Q(aparato_specifico__icontains=query) |
            Q(marca__icontains=query) |
            Q(modelo__icontains=query) |
            Q(falla_descrita__icontains=query) |
            Q(id__icontains=query)
        )
        
    context = {
        'ordenes': ordenes_pendientes,
        'ordenes_entregadas': ordenes_entregadas,
        'clientes_facturacion': clientes_facturacion,
        'repuestos': repuestos, # <-- Enviamos los repuestos al HTML
    }
    return render(request, 'reparaciones/dashboard.html', context)


def crear_orden(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_cliente')
        telefono = request.POST.get('telefono_cliente')
        categoria = request.POST.get('categoria')
        aparato = request.POST.get('aparato_specifico')
        marca = request.POST.get('marca')
        modelo = request.POST.get('modelo', '')
        falla = request.POST.get('falla_descrita', '')

        OrdenReparacion.objects.create(
            nombre_cliente=nombre,
            telefono_cliente=telefono,
            categoria=categoria,
            aparato_specifico=aparato,
            marca=marca,
            modelo=modelo,
            falla_descrita=falla,
            estado='PENDIENTE'
        )
        messages.success(request, f"✅ Equipo de {nombre} ingresado correctamente.")
    return redirect('reparaciones:dashboard')


# NUEVO: VISTA PARA GUARDAR UN NUEVO REPUESTO EN EL INVENTARIO
def crear_repuesto(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        nombre = request.POST.get('nombre', '').strip()
        cantidad = request.POST.get('cantidad', 1)
        precio = request.POST.get('precio', 0.00)

        # Evitar duplicados de código
        if Repuesto.objects.filter(codigo=codigo).exists():
            messages.warning(request, f"⚠️ El código '{codigo}' ya existe en el inventario.")
        else:
            Repuesto.objects.create(
                codigo=codigo,
                nombre=nombre,
                cantidad=int(cantidad),
                precio=float(precio)
            )
            messages.success(request, f"📦 Repuesto '{nombre}' agregado al inventario exitosamente.")
            
    return redirect('reparaciones:dashboard')


def actualizar_orden(request, orden_id):
    orden = get_object_or_404(OrdenReparacion, id=orden_id)
    if request.method == 'POST':
        if 'monto_cotizacion' in request.POST:
            try:
                orden.monto_cotizacion = float(request.POST.get('monto_cotizacion', 0))
            except ValueError:
                pass
        if 'dias_garantia' in request.POST:
            try:
                orden.dias_garantia = int(request.POST.get('dias_garantia', 10))
            except ValueError:
                pass
        if 'nuevo_estado' in request.POST:
            nuevo = request.POST.get('nuevo_estado')
            if nuevo in dict(OrdenReparacion.ESTADOS).keys():
                orden.estado = nuevo
        orden.save()
        messages.success(request, f"☑️ Datos de la orden #{orden.id} guardados correctamente.")
    return redirect('reparaciones:dashboard')


def actualizar_cliente(request, cliente_id):
    cliente = get_object_or_404(ClienteFacturacion, id=cliente_id)
    if request.method == 'POST':
        cliente.nombre = request.POST.get('nombre', cliente.nombre)
        cliente.rfc = request.POST.get('rfc', '')
        cliente.email = request.POST.get('email', '')
        cliente.direccion = request.POST.get('direccion', '')
        cliente.save()
        messages.success(request, f"☑️ Datos fiscales de {cliente.nombre} guardados exitosamente.")
    return redirect('reparaciones:dashboard')


def cambiar_estado(request, orden_id, nuevo_estado):
    orden = get_object_or_404(OrdenReparacion, id=orden_id)
    if nuevo_estado in dict(OrdenReparacion.ESTADOS).keys():
        orden.estado = nuevo_estado
        orden.save()
    return redirect('reparaciones:dashboard')


def entregar_orden(request, orden_id):
    orden = get_object_or_404(OrdenReparacion, id=orden_id)
    factura = request.GET.get('factura', 'no')
    
    orden.estado = 'ENTREGADO'
    orden.fecha_entrega = timezone.now()
    
    if factura == 'si':
        orden.requiere_factura = True
        ClienteFacturacion.objects.get_or_create(
            telefono=orden.telefono_cliente,
            defaults={'nombre': orden.nombre_cliente}
        )
        url_wa = orden.get_wa_facturacion_url()
        msg = f'🤖 <strong>BOT DE FACTURACIÓN:</strong> Orden #{orden.id} terminada. Solicite los datos fiscales al cliente por WhatsApp:<br><a href="{url_wa}" target="_blank" class="btn btn-sm btn-success mt-2 fw-bold shadow"><i class="bi bi-whatsapp me-1"></i> Enviar Mensaje de Facturación</a>'
        messages.success(request, msg)
    else:
        messages.info(request, f"☑️ Orden #{orden.id} cobrada y entregada (Nota simple / Sin factura).")
        
    orden.save()
    return redirect('reparaciones:dashboard')