# models.py
import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date
from sqlalchemy import Boolean, Column
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.types import DECIMAL, Enum 
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, DateTime

class RolEnum(PyEnum):
    vendedor = "vendedor"
    administrador = "administrador"

class RoleModel(Base):
    __tablename__ = 'roles'

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(Enum(RolEnum))

    # Relación inversa con UsuarioModel
    usuarios = relationship("UsuarioModel", back_populates="rol")


class UsuarioModel(Base):
    __tablename__ = 'usuarios'

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    contraseña = Column(String)
    telefono = Column(String)
    fecha_contratacion = Column(DateTime, default=datetime.utcnow)
    id_rol = Column(Integer, ForeignKey('roles.id_rol'))  # Relación con roles
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    ordenes = relationship("OrdenProveedorModel", back_populates="usuario")
    movimientos = relationship("MovimientoInventario", back_populates="usuario")
    rol = relationship("RoleModel", back_populates="usuarios")

class ClienteModel(Base):
    __tablename__ = 'clientes'

    id_cliente = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    telefono = Column(String)
    direccion = Column(String)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    nivel_membresia = Column(String)  
    frecuencia_compra = Column(String)

    notificaciones = relationship("NotificacionClienteModel", back_populates="cliente")


class LeidaEnum(str, enum.Enum):
    no = "no"
    si = "si"

class NotificacionClienteModel(Base):
    __tablename__ = "notificacionesclientes"

    id_notificacion = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('clientes.id_cliente'))
    id_promocion = Column(Integer, ForeignKey('promociones.id_promocion'))
    titulo = Column(String(255))
    mensaje = Column(String)
    fecha_envio = Column(DateTime, default=datetime.utcnow)
    leida = Column(Enum('no', 'si', name="leida_enum"))

    cliente = relationship("ClienteModel", back_populates="notificaciones")
    promocion = relationship("PromocionModel", back_populates="notificaciones")


class PromocionModel(Base):
    __tablename__ = 'promociones'

    id_promocion = Column(Integer, primary_key=True, index=True)
    id_producto = Column(Integer)
    descripcion = Column(String(255))
    descuento = Column(DECIMAL(5, 2))
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    estado = Column(Enum('activa', 'inactiva'))

    notificaciones = relationship("NotificacionClienteModel", back_populates="promocion")


class ProductoModel(Base):
    __tablename__ = 'productos'

    id_producto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    descripcion = Column(Text)
    categoria = Column(Enum('comic', 'figura de colección'))
    stock_actual = Column(Integer)
    stock_minimo = Column(Integer)
    precio = Column(DECIMAL(10, 2))
    editorial_o_marca = Column(String(100))
    fecha_lanzamiento = Column(Date)
    imagen_url = Column(String(255), nullable=True)
    id_proveedor = Column(Integer, ForeignKey('proveedores.id_proveedor'))

    proveedor = relationship("ProveedorModel", back_populates="productos")
    ordenes = relationship("OrdenProveedorModel", back_populates="producto")  
    movimientos = relationship("MovimientoInventario", back_populates="producto")# Correcta relación inversa con OrdenProveedorModel


class ProveedorModel(Base):
    __tablename__ = 'proveedores'

    id_proveedor = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    email = Column(String(100))
    telefono = Column(String(15))
    direccion = Column(String(255))
    fecha_ultimo_abastecimiento = Column(DateTime)
    calificacion = Column(Integer)

    productos = relationship("ProductoModel", back_populates="proveedor")
    ordenes = relationship("OrdenProveedorModel", back_populates="proveedor")
    recepciones = relationship("RecepcionMercanciaModel", back_populates="proveedor")


class OrdenProveedorModel(Base):
    __tablename__ = 'ordenesproveedores'

    id_orden = Column(Integer, primary_key=True, index=True)
    id_proveedor = Column(Integer, ForeignKey('proveedores.id_proveedor'))
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'))
    id_producto = Column(Integer, ForeignKey('productos.id_producto'))
    cantidad = Column(Integer)
    estado = Column(String(50), default="pendiente")
    fecha_orden = Column(DateTime, default=datetime.now)


    # Relaciones con otros modelos
    proveedor = relationship("ProveedorModel", back_populates="ordenes")
    usuario = relationship("UsuarioModel", back_populates="ordenes")
    producto = relationship("ProductoModel", back_populates="ordenes")  # Relación con ProductoModel



# SQLAlchemy Model
class RecepcionMercanciaModel(Base):
    __tablename__ = 'recepcionesmercancia'

    id_recepcion = Column(Integer, primary_key=True, index=True)
    id_proveedor = Column(Integer, ForeignKey('proveedores.id_proveedor'))
    almacen = Column(String(100))
    fecha_recepcion = Column(Date)
    fecha_documento = Column(Date, nullable=True)
    numero_documento = Column(String(50), nullable=True)
    tipo_producto = Column(String(100))
    cantidad = Column(Integer)
    marca = Column(String(50))
    estatus = Column(String(50))
    total = Column(DECIMAL(10, 2))

    proveedor = relationship("ProveedorModel", back_populates="recepciones")



class TipoMovimiento(PyEnum):
    entrada = "entrada"
    salida = "salida"
    ajuste = "ajuste"
    alerta = "alerta"

# Modelo SQLAlchemy para movimientos de inventario
class MovimientoInventario(Base):
    __tablename__ = 'movimientosinventario'

    id_movimiento = Column(Integer, primary_key=True, index=True)
    id_producto = Column(Integer, ForeignKey('productos.id_producto'))
    tipo_movimiento = Column(Enum(TipoMovimiento), nullable=False)  # Usamos Enum para tipo de movimiento
    cantidad = Column(Integer)
    nivel_actual = Column(Integer)
    nivel_minimo = Column(Integer)
    fecha_movimiento = Column(DateTime, default=datetime.utcnow)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario')) 
    id_orden = Column(Integer, nullable=True)

    # Relación con otras tablas, si es necesario
    producto = relationship("ProductoModel", back_populates="movimientos")
    usuario = relationship("UsuarioModel", back_populates="movimientos")



