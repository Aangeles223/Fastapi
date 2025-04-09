from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas import OrdenProveedorCreate, ProveedorCreate
from schemas import  Producto, ProductoCreate, Usuario as UsuarioSchema, UsuarioCreate, Cliente as ClienteSchema, ClienteCreate, NotificacionCliente, NotificacionClienteCreate, Promocion, PromocionCreate
from database import SessionLocal
import bcrypt 
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta 
from schemas import OrdenProveedorBase
from schemas import OrdenProveedorCreate
from models import UsuarioModel, ClienteModel, NotificacionClienteModel, PromocionModel, ProductoModel, ProveedorModel, OrdenProveedorModel, RecepcionMercanciaModel, MovimientoInventario, UsuarioModel, RoleModel
from schemas import Proveedor, RecepcionMercanciaBase, RecepcionMercanciaCreate, MovimientoInventarioCreate, MovimientoInventarioResponse, UsuarioCreate, RoleResponse
from fastapi.middleware.cors import CORSMiddleware


# Crea una instancia de FastAPI
app = FastAPI()



# Clave secreta para JWT
SECRET_KEY = "tu_secreto"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependencia que proporciona la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoints

# ------------------------------------- #
# 🔹 GESTION LOGIN                     #
# ------------------------------------- #

@app.post("/api/login", tags=["Login"])
def login(form_data: UsuarioCreate, db: Session = Depends(get_db)):
    # Buscar el usuario en la base de datos
    usuario = db.query(UsuarioModel).filter(UsuarioModel.email == form_data.email).first()
    
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar la contraseña
    if not bcrypt.checkpw(form_data.contraseña.encode(), usuario.contraseña.encode()):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    # Generar token JWT
    token_expires = timedelta(hours=1)
    token = jwt.encode(
        {"sub": usuario.email, "id_usuario": usuario.id_usuario, "exp": datetime.utcnow() + token_expires},
        SECRET_KEY, 
        algorithm="HS256"
    )

    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/login/empleado", tags=["Login"])
def login_empleado(form_data: UsuarioCreate, db: Session = Depends(get_db)):
    # Buscar el usuario con rol de empleado (suponiendo que el id_rol = 2 es para empleados)
    usuario = db.query(UsuarioModel).filter(UsuarioModel.email == form_data.email, UsuarioModel.id_rol == 2).first()
    
    if usuario is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Verificar la contraseña
    if not bcrypt.checkpw(form_data.contraseña.encode(), usuario.contraseña.encode()):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    
    # Generar token JWT
    token_expires = timedelta(hours=1)
    token = jwt.encode(
        {"sub": usuario.email, "id_usuario": usuario.id_usuario, "exp": datetime.utcnow() + token_expires},
        SECRET_KEY, 
        algorithm="HS256"
    )

    return {"access_token": token, "token_type": "bearer", "usuario": usuario}


# ------------------------------------- #
# 🔹 GESTION USUARIOS                 #
# ------------------------------------- #

# Obtener todos los usuarios
@app.get("/api/usuarios", response_model=List[UsuarioSchema], tags=["Usuarios"])
def get_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(UsuarioModel).all()
    return usuarios  # Pydantic se encargará de la conversión

# Obtener un usuario por ID
@app.get("/api/usuarios/{usuario_id}", response_model=UsuarioSchema, tags=["Usuarios"])
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario  # Pydantic se encargará de la conversión

# Crear un nuevo usuario
@app.post("/api/usuarios", response_model=UsuarioSchema, tags=["Usuarios"])
def create_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Cifrar la contraseña
    hashed_password = bcrypt.hashpw(usuario.contraseña.encode('utf-8'), bcrypt.gensalt())

    # Crear el usuario con la contraseña cifrada y la fecha de contratación
    new_usuario = UsuarioModel(
        nombre=usuario.nombre,
        email=usuario.email,
        telefono=usuario.telefono,
        contraseña=hashed_password,  # Guardamos el hash de la contraseña
        fecha_contratacion=datetime.utcnow(),  # Establecer fecha de contratación
        id_rol=usuario.id_rol,  # Asumiendo que también pasas el id_rol
        activo=True  # O puedes asignar 'True' o el valor que corresponda según tu lógica
    )
    db.add(new_usuario)
    db.commit()
    db.refresh(new_usuario)
    return new_usuario


# Actualizar un usuario
@app.put("/api/usuarios/{usuario_id}", response_model=UsuarioSchema, tags=["Usuarios"])
def update_usuario(usuario_id: int, usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Buscar el usuario en la base de datos
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Si la contraseña está incluida en la solicitud, la ciframos y la actualizamos
    if usuario.contraseña:
        hashed_password = bcrypt.hashpw(usuario.contraseña.encode('utf-8'), bcrypt.gensalt())
        db_usuario.contraseña = hashed_password

    # Actualizar los campos del usuario
    db_usuario.nombre = usuario.nombre
    db_usuario.email = usuario.email
    db_usuario.telefono = usuario.telefono
    db_usuario.id_rol = usuario.id_rol
    db_usuario.activo = usuario.activo  # Asegúrate de que 'activo' esté en el esquema de Pydantic

    db.commit()
    db.refresh(db_usuario)  # Refrescar el objeto para obtener los datos actualizados
    return db_usuario  # Pydantic se encargará de la conversión



# Eliminar un usuario
@app.delete("/api/usuarios/{usuario_id}", tags=["Usuarios"])
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(db_usuario)
    db.commit()
    return {"detail": "Usuario eliminado"}

# Obtener todos los roles
@app.get("/api/roles", response_model=list[RoleResponse], tags=["Usuarios"])
def get_roles(db: Session = Depends(get_db)):
    return db.query(RoleModel).all()


# ------------------------------------- #
# 🔹 GESTION DE CLIENTES                #
# ------------------------------------- #

# Obtener todos los clientes
@app.get("/api/clientes", response_model=List[ClienteSchema], tags=["Clientes"])
def get_clientes(db: Session = Depends(get_db)):
    clientes = db.query(ClienteModel).all()
    return clientes  # Pydantic convertirá automáticamente los datos

# Obtener un cliente por ID
@app.get("/api/clientes/{cliente_id}", response_model=ClienteSchema, tags=["Clientes"])
def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id_cliente == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# Crear un nuevo cliente
@app.post("/api/clientes", response_model=ClienteSchema, tags=["Clientes"])
def create_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = db.query(ClienteModel).filter(ClienteModel.email == cliente.email).first()
    if db_cliente:
        raise HTTPException(status_code=400, detail="El cliente ya existe")
    
    # Elimina la parte de cifrado de contraseña
    new_cliente = ClienteModel(
        nombre=cliente.nombre,
        email=cliente.email,
        telefono=cliente.telefono,
        direccion=cliente.direccion,
        nivel_membresia=cliente.nivel_membresia,
        frecuencia_compra=cliente.frecuencia_compra
    )
    
    print("Agregando cliente...")
    db.add(new_cliente)
    
    try:
        print("Commiting...")
        db.commit()  # Guardar en la base de datos
        print("Commit realizado")
    except Exception as e:
        print(f"Error en commit: {e}")
        db.rollback()  # En caso de error revertir
        raise HTTPException(status_code=500, detail=f"Error al crear cliente: {str(e)}")
    
    db.refresh(new_cliente)  # Asegurarse de que el objeto se refresque con los datos más recientes
    return new_cliente



# Actualizar un cliente
@app.put("/api/clientes/{cliente_id}", response_model=ClienteSchema, tags=["Clientes"])
def update_cliente(cliente_id: int, cliente: ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = db.query(ClienteModel).filter(ClienteModel.id_cliente == cliente_id).first()
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Actualizar los campos del cliente, sin la 'contraseña'
    db_cliente.nombre = cliente.nombre
    db_cliente.email = cliente.email
    db_cliente.telefono = cliente.telefono
    db_cliente.direccion = cliente.direccion
    db_cliente.nivel_membresia = cliente.nivel_membresia
    db_cliente.frecuencia_compra = cliente.frecuencia_compra
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


# Eliminar un cliente
@app.delete("/api/clientes/{cliente_id}", tags=["Clientes"])
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = db.query(ClienteModel).filter(ClienteModel.id_cliente == cliente_id).first()
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db.delete(db_cliente)
    db.commit()
    return {"detail": "Cliente eliminado"}


# ------------------------------------- #
# 🔹 GESTION NOTIFICACIONES             #
# ------------------------------------- #


# Endpoint para obtener todas las notificaciones
@app.get("/api/notificaciones", response_model=List[NotificacionCliente], tags=["Notificaciones"])
def get_notificaciones(db: Session = Depends(get_db)):
    notificaciones = db.query(NotificacionClienteModel).order_by(NotificacionClienteModel.fecha_envio.desc()).all()
    return notificaciones

# Endpoint para obtener notificación por ID
@app.get("/api/notificaciones/{notificacion_id}", response_model=NotificacionCliente, tags=["Notificaciones"])
def get_notificacion(notificacion_id: int, db: Session = Depends(get_db)):
    notificacion = db.query(NotificacionClienteModel).filter(NotificacionClienteModel.id_notificacion == notificacion_id).first()
    if notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notificacion

# Endpoint para crear una nueva notificación
@app.post("/api/notificaciones", response_model=NotificacionCliente, tags=["Notificaciones"])
def create_notificacion(notificacion: NotificacionClienteCreate, db: Session = Depends(get_db)):
    # Verificar si el cliente existe
    cliente = db.query(ClienteModel).filter(ClienteModel.id_cliente == notificacion.id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Verificar si la promoción existe
    promocion = db.query(PromocionModel).filter(PromocionModel.id_promocion == notificacion.id_promocion).first()
    if not promocion:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")
    
    # Crear la notificación
    new_notificacion = NotificacionClienteModel(
        id_cliente=notificacion.id_cliente,
        id_promocion=notificacion.id_promocion,
        titulo=notificacion.titulo,
        mensaje=notificacion.mensaje,
        leida=notificacion.leida
    )
    
    db.add(new_notificacion)
    db.commit()
    db.refresh(new_notificacion)
    return new_notificacion


# Endpoint para marcar una notificación como leída
@app.put("/api/notificaciones/{notificacion_id}/leida", response_model=NotificacionCliente, tags=["Notificaciones"])
def mark_as_read(notificacion_id: int, db: Session = Depends(get_db)):
    db_notificacion = db.query(NotificacionClienteModel).filter(NotificacionClienteModel.id_notificacion == notificacion_id).first()
    if db_notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    # Cambiar 'True' por 'si' para que sea un valor válido del Enum
    db_notificacion.leida = 'si'  # Usamos 'si' o 'no' según el caso
    db.commit()
    db.refresh(db_notificacion)
    return db_notificacion


# Endpoint para eliminar una notificación
@app.delete("/api/notificaciones/{notificacion_id}", tags=["Notificaciones"])
def delete_notificacion(notificacion_id: int, db: Session = Depends(get_db)):
    db_notificacion = db.query(NotificacionClienteModel).filter(NotificacionClienteModel.id_notificacion == notificacion_id).first()
    if db_notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    db.delete(db_notificacion)
    db.commit()
    return {"detail": "Notificación eliminada"}


# ------------------------------------- #
# 🔹 GESTION PROMOCIONES             #
# ------------------------------------- #

# Obtener todas las promociones
@app.get("/api/promociones", tags=["Promociones"])
def get_promociones(db: Session = Depends(get_db)):
    promociones = db.query(PromocionModel).all()
    # Convertir fechas a cadenas de texto
    for promocion in promociones:
        promocion.fecha_inicio = promocion.fecha_inicio.isoformat()
        promocion.fecha_fin = promocion.fecha_fin.isoformat()
    return promociones


# Obtener una promoción por ID
@app.get("/api/promociones/{promocion_id}", response_model=Promocion, tags=["Promociones"])
def get_promocion(promocion_id: int, db: Session = Depends(get_db)):
    promocion = db.query(PromocionModel).filter(PromocionModel.id_promocion == promocion_id).first()
    if promocion is None:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")
    return promocion

# Crear una nueva promoción
# Crear una nueva promoción
@app.post("/api/promociones", tags=["Promociones"])
def create_promocion(promocion: PromocionCreate, db: Session = Depends(get_db)):
    try:
        new_promocion = PromocionModel(
            id_producto=promocion.id_producto,  # Asumiendo que id_producto es necesario
            descripcion=promocion.descripcion,
            fecha_inicio=promocion.fecha_inicio,
            fecha_fin=promocion.fecha_fin,
            descuento=promocion.descuento,
            estado=promocion.estado  # Añadí 'estado' al crear la promoción
        )
        db.add(new_promocion)
        db.commit()
        db.refresh(new_promocion)
        return new_promocion
    except Exception as e:
        db.rollback()  # Rollback en caso de error
        print(f"Error al insertar promoción: {e}")
        raise HTTPException(status_code=500, detail="Error en la base de datos")


# Actualizar una promoción existente
@app.put("/api/promociones/{promocion_id}", response_model=Promocion, tags=["Promociones"])
def update_promocion(promocion_id: int, promocion: PromocionCreate, db: Session = Depends(get_db)):
    db_promocion = db.query(PromocionModel).filter(PromocionModel.id_promocion == promocion_id).first()
    if db_promocion is None:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")

    db_promocion.descripcion = promocion.descripcion
    db_promocion.descuento = promocion.descuento
    db_promocion.fecha_inicio = promocion.fecha_inicio
    db_promocion.fecha_fin = promocion.fecha_fin
    db_promocion.estado = promocion.estado  # Mantén la actualización del estado
    db.commit()
    db.refresh(db_promocion)
    return db_promocion


# Eliminar una promoción
@app.delete("/api/promociones/{promocion_id}", tags=["Promociones"])
def delete_promocion(promocion_id: int, db: Session = Depends(get_db)):
    db_promocion = db.query(PromocionModel).filter(PromocionModel.id_promocion == promocion_id).first()
    if db_promocion is None:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")

    db.delete(db_promocion)
    db.commit()
    return {"detail": "Promoción eliminada"}


# ------------------------------------- #
# 🔹 GESTION PRODUCTOS           #
# ------------------------------------- #


@app.get("/api/productos", response_model=List[Producto], tags=["Producto"])
def get_productos(db: Session = Depends(get_db)):
    productos = db.query(ProductoModel).all()  # Esto devuelve objetos SQLAlchemy
    # Convertir 'fecha_lanzamiento' a string
    for producto in productos:
        producto.fecha_lanzamiento = producto.fecha_lanzamiento.isoformat()  # Convertir a string
    return productos  # Esto automáticamente convertirá los resultados en objetos Pydantic


@app.get("/api/productos/{producto_id}", response_model=Producto, tags=["Producto"])
def get_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(ProductoModel).filter(ProductoModel.id_producto == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Producto.from_orm(producto)


@app.post("/api/productos", response_model=Producto, tags=["Producto"])
def create_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    new_producto = ProductoModel(
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        categoria=producto.categoria,
        stock_actual=producto.stock_actual,
        stock_minimo=producto.stock_minimo,
        precio=producto.precio,
        editorial_o_marca=producto.editorial_o_marca,
        fecha_lanzamiento=producto.fecha_lanzamiento,
        imagen_url=producto.imagen_url,
        id_proveedor=producto.id_proveedor
    )
    db.add(new_producto)
    db.commit()
    db.refresh(new_producto)
    return Producto.from_orm(new_producto)

# Endpoint para actualizar un producto existente
@app.put("/api/productos/{producto_id}", response_model=Producto, tags=["Producto"])
def update_producto(producto_id: int, producto: ProductoCreate, db: Session = Depends(get_db)):
    db_producto = db.query(ProductoModel).filter(ProductoModel.id_producto == producto_id).first()
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Validate id_proveedor
    if producto.id_proveedor is not None:
        db_proveedor = db.query(ProveedorModel).filter(ProveedorModel.id_proveedor == producto.id_proveedor).first()
        if db_proveedor is None:
            raise HTTPException(status_code=400, detail="Proveedor no válido")

    # Update product fields
    db_producto.nombre = producto.nombre
    db_producto.descripcion = producto.descripcion
    db_producto.categoria = producto.categoria
    db_producto.stock_actual = producto.stock_actual
    db_producto.stock_minimo = producto.stock_minimo
    db_producto.precio = producto.precio
    db_producto.editorial_o_marca = producto.editorial_o_marca
    db_producto.imagen_url = producto.imagen_url
    db_producto.id_proveedor = producto.id_proveedor

    # Ensure fecha_lanzamiento is properly handled
    if isinstance(producto.fecha_lanzamiento, datetime):
        db_producto.fecha_lanzamiento = producto.fecha_lanzamiento
    else:
        db_producto.fecha_lanzamiento = datetime.fromisoformat(producto.fecha_lanzamiento)

    db.commit()
    db.refresh(db_producto)

    # Convert fecha_lanzamiento to string for the response
    db_producto.fecha_lanzamiento = db_producto.fecha_lanzamiento.isoformat()

    return db_producto



# Endpoint para eliminar un producto
# Eliminar un producto
@app.delete("/api/productos/{producto_id}", tags=["Producto"])
def delete_producto(producto_id: int, db: Session = Depends(get_db)):
    db_producto = db.query(ProductoModel).filter(ProductoModel.id_producto == producto_id).first()
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(db_producto)
    db.commit()
    return {"detail": "Producto eliminado"}



# ------------------------------------- #
# 🔹 GESTION PROVEEDORES                #
# ------------------------------------- #

@app.get("/api/proveedores", response_model=List[Proveedor], tags=["Proveedor"])  # Usa List[Proveedor] en lugar de list[Proveedor]
def get_proveedores(db: Session = Depends(get_db)):
    proveedores = db.query(ProveedorModel).all()  # SQLAlchemy Model
    return proveedores

# Obtener un proveedor por ID
@app.get("/api/proveedores/{proveedor_id}", response_model=Proveedor, tags=["Proveedor"])
def get_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    proveedor = db.query(ProveedorModel).filter(ProveedorModel.id_proveedor == proveedor_id).first()  # Usar ProveedorModel
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


# Crear un nuevo proveedor
@app.post("/api/proveedores", response_model=Proveedor, tags=["Proveedor"])
def create_proveedor(proveedor: ProveedorCreate, db: Session = Depends(get_db)):
    # Check if the email already exists
    existing_proveedor = db.query(ProveedorModel).filter(ProveedorModel.email == proveedor.email).first()  # Aquí usa ProveedorModel
    if existing_proveedor:
        raise HTTPException(status_code=400, detail="El email del proveedor ya existe")

    # Create the new proveedor
    db_proveedor = ProveedorModel(**proveedor.dict())  # Aquí también usa ProveedorModel
    db.add(db_proveedor)
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor


# Actualizar un proveedor
@app.put("/api/proveedores/{proveedor_id}", response_model=Proveedor, tags=["Proveedor"])
def update_proveedor(proveedor_id: int, proveedor: ProveedorCreate, db: Session = Depends(get_db)):
    db_proveedor = db.query(ProveedorModel).filter(ProveedorModel.id_proveedor == proveedor_id).first()  # Usar ProveedorModel
    if db_proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    for key, value in proveedor.dict().items():
        setattr(db_proveedor, key, value)
    
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor

# Eliminar un proveedor
@app.delete("/api/proveedores/{proveedor_id}", tags=["Proveedor"])
def delete_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    db_proveedor = db.query(ProveedorModel).filter(ProveedorModel.id_proveedor == proveedor_id).first()  # Usar ProveedorModel
    if db_proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    db.delete(db_proveedor)
    db.commit()
    return {"detail": "Proveedor eliminado"}





# ------------------------------------- #
# 🔹 GESTION ORDENES PROVEEDOR          #
# ------------------------------------- #

# Obtenrer todas las ordenes de proveedor
@app.get("/api/ordenesproveedor", response_model=List[OrdenProveedorBase], tags=["Ordenes"])
def get_ordenesproveedor(db: Session = Depends(get_db)):
    ordenes = db.query(OrdenProveedorModel).all()
    # Convertir `fecha_orden` de datetime a date antes de devolver la respuesta
    for orden in ordenes:
        orden.fecha_orden = orden.fecha_orden.date()  # Convertir a solo fecha
    return ordenes

# Crear una nueva orden de proveedor
@app.post("/api/ordenesproveedor", response_model=OrdenProveedorBase, tags=["Ordenes"])
def create_ordenproveedor(orden: OrdenProveedorCreate, db: Session = Depends(get_db)):
    db_orden = OrdenProveedorModel(**orden.dict())  # Creamos el objeto de la base de datos
    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)
    return db_orden


# Obtener una orden de proveedor por ID
@app.get("/api/ordenesproveedor/{id_orden}", response_model=OrdenProveedorBase, tags=["Ordenes"])
def get_ordenproveedor(id_orden: int, db: Session = Depends(get_db)):
    db_orden = db.query(OrdenProveedorModel).filter(OrdenProveedorModel.id_orden == id_orden).first()
    if db_orden is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return db_orden  # La fecha_orden será convertida correctamente a datetime (solo con fecha)


# Actualizar una orden de proveedor
@app.put("/api/ordenesproveedor/{id_orden}", response_model=OrdenProveedorBase, tags=["Ordenes"])
def update_ordenproveedor(id_orden: int, orden: OrdenProveedorCreate, db: Session = Depends(get_db)):
    db_orden = db.query(OrdenProveedorModel).filter(OrdenProveedorModel.id_orden == id_orden).first()
    if db_orden is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    for key, value in orden.dict().items():
        setattr(db_orden, key, value)
    
    db.commit()
    db.refresh(db_orden)
    return db_orden


# Eliminar una orden de proveedor
@app.delete("/api/ordenesproveedor/{id_orden}", tags=["Ordenes"])
def delete_ordenproveedor(id_orden: int, db: Session = Depends(get_db)):
    db_orden = db.query(OrdenProveedorModel).filter(OrdenProveedorModel.id_orden == id_orden).first()
    if db_orden is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    db.delete(db_orden)
    db.commit()
    return {"detail": "Orden eliminada"}



# ------------------------------------- #
# 🔹 GESTION RECEPCION DE MERCANCIA     #
# ------------------------------------- #

@app.get("/api/recepciones", response_model=List[RecepcionMercanciaBase], tags=["Mercancias"])
def get_recepciones(
    numero_documento: Optional[str] = None,
    palabra_clave: Optional[str] = None,
    tipo_producto: Optional[str] = None,
    estatus: Optional[str] = None,
    proveedor: Optional[str] = None,
    almacen: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(RecepcionMercanciaModel).join(ProveedorModel, RecepcionMercanciaModel.id_proveedor == ProveedorModel.id_proveedor)
    
    if numero_documento:
        query = query.filter(RecepcionMercanciaModel.numero_documento.like(f"%{numero_documento}%"))
    if palabra_clave:
        query = query.filter(RecepcionMercanciaModel.marca.like(f"%{palabra_clave}%"))
    if tipo_producto:
        query = query.filter(RecepcionMercanciaModel.tipo_producto == tipo_producto)
    if estatus:
        query = query.filter(RecepcionMercanciaModel.estatus == estatus)
    if proveedor:
        query = query.filter(ProveedorModel.nombre.like(f"%{proveedor}%"))
    if almacen:
        query = query.filter(RecepcionMercanciaModel.almacen.like(f"%{almacen}%"))
    
    # Imprime o registra la consulta para ver qué se está ejecutando
    print(query.statement)  # O usa logging para imprimir
    
    recepciones = query.order_by(RecepcionMercanciaModel.id_recepcion.desc()).all()
    
    if not recepciones:
        print("No se encontraron recepciones con los parámetros dados.")
    
    return recepciones




@app.get("/api/recepciones/{id_recepcion}", response_model=RecepcionMercanciaBase, tags=["Mercancias"])
def get_recepcion(id_recepcion: int, db: Session = Depends(get_db)):
    db_recepcion = db.query(RecepcionMercanciaModel).filter(RecepcionMercanciaModel.id_recepcion == id_recepcion).first()
    if db_recepcion is None:
        raise HTTPException(status_code=404, detail="Recepción no encontrada")
    return db_recepcion



@app.post("/api/recepciones", response_model=RecepcionMercanciaBase, tags=["Mercancias"])
def create_recepcion(recepcion: RecepcionMercanciaCreate, db: Session = Depends(get_db)):
    # Elimina la referencia a 'numero' si no es necesaria
    db_recepcion = RecepcionMercanciaModel(
        id_proveedor=recepcion.id_proveedor,
        almacen=recepcion.almacen,
        fecha_recepcion=recepcion.fecha_recepcion,
        fecha_documento=recepcion.fecha_documento,
        numero_documento=recepcion.numero_documento,
        tipo_producto=recepcion.tipo_producto,
        cantidad=recepcion.cantidad,
        marca=recepcion.marca,
        estatus=recepcion.estatus,
        total=recepcion.total
    )
    db.add(db_recepcion)
    db.commit()
    db.refresh(db_recepcion)
    return db_recepcion



@app.put("/api/recepciones/{id_recepcion}", response_model=RecepcionMercanciaBase, tags=["Mercancias"])
def update_recepcion(id_recepcion: int, recepcion: RecepcionMercanciaCreate, db: Session = Depends(get_db)):
    db_recepcion = db.query(RecepcionMercanciaModel).filter(RecepcionMercanciaModel.id_recepcion == id_recepcion).first()
    if db_recepcion is None:
        raise HTTPException(status_code=404, detail="Recepción no encontrada")
    
    # Actualizar campos
    for key, value in recepcion.dict().items():
        setattr(db_recepcion, key, value)
    
    db.commit()
    db.refresh(db_recepcion)
    return db_recepcion


@app.delete("/api/recepciones/{id_recepcion}", tags=["Mercancias"])
def delete_recepcion(id_recepcion: int, db: Session = Depends(get_db)):
    db_recepcion = db.query(RecepcionMercanciaModel).filter(RecepcionMercanciaModel.id_recepcion == id_recepcion).first()
    if db_recepcion is None:
        raise HTTPException(status_code=404, detail="Recepción no encontrada")
    
    db.delete(db_recepcion)
    db.commit()
    return {"detail": "Recepción eliminada"}




# ---------------------------- #
# GESTION MOVIMIENTOS          #
# ---------------------------- #


# Obtener los movimientos
@app.get("/api/movimientos", response_model=List[MovimientoInventarioResponse], tags=["Movimientos"])
def get_movimientos(db: Session = Depends(get_db)):
    movimientos = db.query(MovimientoInventario).all()
    return movimientos

@app.get("/api/movimientos/{id}", response_model=MovimientoInventarioResponse, tags=["Movimientos"])
def get_movimiento(id: int, db: Session = Depends(get_db)):
    db_movimiento = db.query(MovimientoInventario).filter(MovimientoInventario.id_movimiento == id).first()
    
    if not db_movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    
    return db_movimiento

# Crear un nuevo movimiento
@app.post("/api/movimientos", response_model=MovimientoInventarioResponse, tags=["Movimientos"])
def create_movimiento(movimiento: MovimientoInventarioCreate, db: Session = Depends(get_db)):
    # Verificar que el producto exista
    producto = db.query(ProductoModel).filter(ProductoModel.id_producto == movimiento.id_producto).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Crear el nuevo movimiento
    db_movimiento = MovimientoInventario(
        tipo_movimiento=movimiento.tipo_movimiento,
        id_producto=movimiento.id_producto,
        cantidad=movimiento.cantidad,
        nivel_actual=movimiento.nivel_actual,
        nivel_minimo=movimiento.nivel_minimo,
        fecha_movimiento=movimiento.fecha_movimiento or datetime.utcnow(),
        id_usuario=movimiento.id_usuario
    )
    
    db.add(db_movimiento)
    db.commit()
    db.refresh(db_movimiento)
    
    return db_movimiento


# Editar un movimiento existente
@app.put("/api/movimientos/{id}", response_model=MovimientoInventarioResponse, tags=["Movimientos"])
def update_movimiento(id: int, movimiento: MovimientoInventarioCreate, db: Session = Depends(get_db)):
    db_movimiento = db.query(MovimientoInventario).filter(MovimientoInventario.id_movimiento == id).first()
    
    if not db_movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    
    # Actualizar el movimiento con nuevos datos
    for key, value in movimiento.dict().items():
        setattr(db_movimiento, key, value)
    
    db.commit()
    db.refresh(db_movimiento)
    return db_movimiento

# Eliminar un movimiento
@app.delete("/api/movimientos/{id}", tags=["Movimientos"])
def delete_movimiento(id: int, db: Session = Depends(get_db)):
    db_movimiento = db.query(MovimientoInventario).filter(MovimientoInventario.id_movimiento == id).first()
    
    if not db_movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    
    db.delete(db_movimiento)
    db.commit()
    return {"message": "Movimiento eliminado correctamente"}


originis = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=originis,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if __name__ =="__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=1000, reload=True)