import decimal
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum
from models import TipoMovimiento



# Modelo para la solicitud de login
class LoginRequest(BaseModel):
    email: str
    password: str


# ---------------------------- #
# 🔹 MODELOS DE USUARIO        #
# ---------------------------- #



class RolEnum(str, Enum):
    vendedor = "vendedor"  
    administrador = "administrador"


class UsuarioBase(BaseModel):
    nombre: Optional[str]
    email: Optional[str]
    telefono: Optional[str]
    id_rol: Optional[int]

class UsuarioCreate(BaseModel):
    nombre: Optional[str]
    email: Optional[str]
    telefono: Optional[str]
    id_rol: Optional[int]
    contraseña: Optional[str]  # Contraseña opcional si no se quiere cambiar
    activo: Optional[bool]

class Usuario(UsuarioBase):
    id_usuario: int
    activo: bool

    class Config:
        orm_mode = True

class UsuarioResponse(UsuarioBase):
    id_usuario: int
    activo: bool

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    nombre_rol: RolEnum

    class Config:
        orm_mode = True

class RoleResponse(RoleBase):
    id_rol: int

# ---------------------------- #
# 🔹 MODELOS DE CLIENTE        #
# ---------------------------- #
class ClienteBase(BaseModel):
    nombre: str
    email: str
    telefono: str
    direccion: str
    nivel_membresia: Optional[str] = None
    frecuencia_compra: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    id_cliente: int

    class Config:
        orm_mode = True


# ---------------------------- #
# 🔹 MODELOS DE NOTIFICACIÓN    #
# ---------------------------- #

class LeidaEnum(str, Enum):
    no = "no"
    si = "si"


class NotificacionClienteBase(BaseModel):
    id_cliente: int
    id_promocion: int
    titulo: str
    mensaje: str
    fecha_envio: Optional[datetime] = None
    leida: Optional[str] = "no"  # Valor por defecto

    class Config:
        orm_mode = True

class NotificacionClienteCreate(NotificacionClienteBase):
    pass

class NotificacionCliente(NotificacionClienteBase):
    id_notificacion: int


# ---------------------------- #
# 🔹 MODELOS DE PROMOCIÓN      #
# ---------------------------- #
class Promocion(BaseModel):
    id_promocion: int
    id_producto: int
    descripcion: str
    descuento: Decimal
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str

    class Config:
        orm_mode = True

class PromocionCreate(BaseModel):
    id_producto: int
    descripcion: str
    descuento: float
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# ---------------------------- #
# 🔹 MODELOS DE PRODUCTO       #
# ---------------------------- #

class Producto(BaseModel):
    nombre: str
    descripcion: str
    categoria: str
    stock_actual: int
    stock_minimo: int
    precio: float
    editorial_o_marca: str
    fecha_lanzamiento: datetime
    imagen_url: Optional[str] = None
    id_proveedor: int

    class Config:
        from_attributes = True


class ProductoCreate(BaseModel):
    nombre: str
    descripcion: str
    categoria: str
    stock_actual: int
    stock_minimo: int
    precio: float
    editorial_o_marca: str
    fecha_lanzamiento: datetime
    imagen_url: Optional[str]
    id_proveedor: int

    class Config:
        orm_mode = True


# ---------------------------- #
# 🔹 MODELOS DE PROVEEDOR      #
# ---------------------------- #
class Proveedor(BaseModel):
    nombre: str
    email: str
    telefono: str
    direccion: str
    fecha_ultimo_abastecimiento: Optional[datetime] = None
    calificacion: Optional[int] = None

class ProveedorCreate(Proveedor):
    pass

class ProveedorWithID(Proveedor):
    id_proveedor: int

    class Config:
        orm_mode = True


# ---------------------------- #
# 🔹 MODELOS DE ORDEN PROVEEDOR#
# ---------------------------- #
class OrdenProveedorBase(BaseModel):
    id_proveedor: int
    id_usuario: int
    id_producto: int
    cantidad: int
    estado: Optional[str] = 'pendiente'
    fecha_orden: datetime

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        # Aseguramos que 'fecha_orden' sea un tipo 'date'
        if isinstance(obj.fecha_orden, datetime):
            obj.fecha_orden = obj.fecha_orden.date()  # Convertimos de datetime a date
        return super().from_orm(obj)

class OrdenProveedorCreate(OrdenProveedorBase):
    pass


# ---------------------------- #
# MODELOS RECEPCION MERCANCIA  #
# ---------------------------- #

# Pydantic Model (Base)
class RecepcionMercanciaBase(BaseModel):
    id_proveedor: int
    almacen: str
    fecha_recepcion: datetime
    fecha_documento: Optional[datetime] = None
    numero_documento: Optional[str] = None
    tipo_producto: str
    cantidad: int
    marca: str
    estatus: str
    total: decimal.Decimal

    class Config:
        orm_mode = True

# Model para Crear (para uso en el POST y PUT)
class RecepcionMercanciaCreate(RecepcionMercanciaBase):
    pass


# ---------------------------- #
# MODELOS MOVIMIENTOS          #
# ---------------------------- #


# Enum para tipo de movimiento
class TipoMovimiento(str, Enum):
    entrada = "entrada"
    salida = "salida"
    ajuste = "ajuste"
    alerta = "alerta"

# Modelo de Pydantic para los movimientos de inventario
class MovimientoInventarioBase(BaseModel):
    tipo_movimiento: TipoMovimiento
    id_producto: int
    cantidad: int
    nivel_actual: Optional[int] = None  # Permitir None en lugar de solo enteros
    nivel_minimo: Optional[int] = None  # Permitir None en lugar de solo enteros
    fecha_movimiento: Optional[datetime] = None
    id_usuario: int

    class Config:
        orm_mode = True

# Para crear nuevos movimientos (POST y PUT)
class MovimientoInventarioCreate(MovimientoInventarioBase):
    pass


# Modelo para la respuesta de movimiento (con ID)
class MovimientoInventarioResponse(MovimientoInventarioBase):
    id_movimiento: int

    class Config:
        orm_mode = True


