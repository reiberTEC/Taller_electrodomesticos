import urllib.parse
from django.db import models
from django.utils import timezone

# 1. MODELO PARA INVENTARIO / EXISTENCIAS
class Repuesto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código / SKU", help_text="Ej. REP-001")
    nombre = models.CharField(max_length=150, verbose_name="Descripción del Repuesto")
    cantidad = models.IntegerField(default=1, verbose_name="Stock disponible")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario ($)")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.cantidad} pzas)"


# 2. MODELO PARA CLIENTES DE FACTURACIÓN
class ClienteFacturacion(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre / Razón Social")
    telefono = models.CharField(max_length=20, unique=True, verbose_name="Teléfono (Contacto)")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    rfc = models.CharField(max_length=20, blank=True, null=True, verbose_name="RFC")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección Fiscal")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.telefono})"

    def get_ordenes_facturadas(self):
        return OrdenReparacion.objects.filter(telefono_cliente=self.telefono, requiere_factura=True).order_by('-fecha_entrega')

    def get_total_facturado(self):
        return sum(o.monto_cotizacion for o in self.get_ordenes_facturadas())


# 3. MODELO PARA ÓRDENES DE REPARACIÓN
class OrdenReparacion(models.Model):
    CATEGORIAS = [
        ('HOGAR', 'Hogar (Lavadoras, Refres, etc.)'),
        ('HERRAMIENTAS', 'Herramientas de trabajo (Taladros, Pulidoras, etc.)'),
        ('CUIDADO', 'Cuidado personal (Secadoras de pelo, Rasuradoras, etc.)'),
        ('OTROS', 'Otros'),
    ]

    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Cotización'),
        ('ACEPTADO', 'Cotización Aceptada (En Reparación)'),
        ('RECHAZADO', 'Cotización No Aceptada / Devuelto'),
        ('REPARADO', 'Listo para Entrega'),
        ('ENTREGADO', 'Entregado y Cobrado'),
    ]

    nombre_cliente = models.CharField(max_length=150, verbose_name="Nombre del Cliente")
    telefono_cliente = models.CharField(max_length=20, verbose_name="Número de Teléfono")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='HOGAR')
    aparato_specifico = models.CharField(max_length=100, verbose_name="¿Qué aparato es?", help_text="Ej. Licuadora 10 velocidades")
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50, blank=True, null=True)
    falla_descrita = models.TextField(verbose_name="Falla descrita por el cliente", blank=True, null=True)

    monto_cotizacion = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Monto Cotizado ($)")
    dias_garantia = models.IntegerField(default=10, verbose_name="Días de Garantía")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    fecha_entrega = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Entrega")
    requiere_factura = models.BooleanField(default=False)

    def __str__(self):
        return f"#{self.id} - {self.aparato_specifico} ({self.nombre_cliente})"

    def _limpiar_telefono(self):
        tel = ''.join(filter(str.isdigit, str(self.telefono_cliente)))
        return f"52{tel}" if not tel.startswith('52') else tel

    def get_wa_cotizacion_url(self):
        tel = self._limpiar_telefono()
        mensaje = (
            f"Hola {self.nombre_cliente}, el Bot de *Taller FixPro* 🤖 le informa que la cotización "
            f"para la reparación de su *{self.aparato_specifico} ({self.marca})* es de *${self.monto_cotizacion}*.\n\n"
            f"¿Desea que procedamos con la reparación?"
        )
        return f"https://api.whatsapp.com/send?phone={tel}&text={urllib.parse.quote(mensaje)}"

    def get_wa_facturacion_url(self):
        tel = self._limpiar_telefono()
        mensaje = (
            f"Hola {self.nombre_cliente}, somos el Bot de Facturación de *Taller FixPro* 🤖.\n\n"
            f"Para generar la factura digital de su *{self.aparato_specifico}*, por favor envíenos por este medio "
            f"su Constancia de Situación Fiscal (PDF), Uso de CFDI y un correo electrónico."
        )
        return f"https://api.whatsapp.com/send?phone={tel}&text={urllib.parse.quote(mensaje)}"