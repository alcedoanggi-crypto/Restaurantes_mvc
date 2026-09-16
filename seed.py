"""Datos de demostración.

Uso:
    python seed.py            # crea tablas y carga demo
    python seed.py --reset    # borra todo y recarga
    flask --app run seed      # equivalente vía CLI
"""
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import (
    Categoria,
    DetallePedido,
    Empleado,
    Factura,
    Insumo,
    Mesa,
    Pedido,
    Platillo,
    Usuario,
)

CATEGORIAS = {
    "Entradas": [
        ("Guacamole con totopos", 95, 8,
         "https://images.unsplash.com/photo-1600335895229-6e75511892c8?auto=format&fit=crop&w=600&q=60"),
        ("Sopa de tortilla", 85, 10,
         "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=600&q=60"),
        ("Queso fundido", 110, 9, None),
    ],
    "Platos fuertes": [
        ("Tacos al pastor (orden)", 145, 12,
         "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&q=60"),
        ("Enchiladas verdes", 165, 15,
         "https://images.unsplash.com/photo-1534352956036-cd81e27dd615?auto=format&fit=crop&w=600&q=60"),
        ("Arrachera 250g", 320, 18, None),
        ("Pescado a la talla", 285, 20, None),
        ("Pasta al pomodoro", 155, 14,
         "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=600&q=60"),
    ],
    "Postres": [
        ("Pastel de tres leches", 78, 5, None),
        ("Flan napolitano", 70, 5, None),
        ("Churros con cajeta", 82, 8, None),
    ],
    "Bebidas": [
        ("Agua fresca de jamaica", 45, 3, None),
        ("Limonada mineral", 55, 3, None),
        ("Refresco", 40, 2, None),
        ("Cerveza artesanal", 75, 2, None),
        ("Café americano", 42, 4, None),
    ],
}

INSUMOS = [
    ("Tortilla de maíz", "kg", 25, 8, 22),
    ("Carne de res", "kg", 12, 5, 210),
    ("Aguacate", "kg", 6, 4, 85),
    ("Queso Oaxaca", "kg", 4, 3, 160),
    ("Jitomate", "kg", 18, 6, 28),
    ("Cebolla", "kg", 15, 5, 24),
    ("Limón", "kg", 9, 4, 30),
    ("Harina", "kg", 20, 8, 18),
    ("Aceite vegetal", "lt", 14, 6, 42),
    ("Refresco (botella)", "pza", 60, 24, 12),
]

EMPLEADOS = [
    ("Ana", "Ramírez", "Gerente", 18000),
    ("Luis", "Hernández", "Mesero", 8000),
    ("Marta", "Gómez", "Mesera", 8000),
    ("Jorge", "Díaz", "Cocinero", 11000),
    ("Sofía", "Torres", "Cajera", 9500),
]

USUARIOS = [
    ("Administrador", "admin", "admin@sobremesa.mx", "admin123", "administrador", 0),
    ("Luis Hernández", "mesero", "mesero@sobremesa.mx", "mesero123", "mesero", 1),
    ("Jorge Díaz", "cocina", "cocina@sobremesa.mx", "cocina123", "cocina", 3),
    ("Sofía Torres", "cajero", "cajero@sobremesa.mx", "cajero123", "cajero", 4),
]


def run_seed(reset: bool = False):
    if reset:
        db.drop_all()
    db.create_all()

    if Usuario.query.first():
        print("La base de datos ya tiene datos. Usa --reset para recargar.")
        return

    # --- Empleados ---
    empleados = []
    for nombre, ap, puesto, salario in EMPLEADOS:
        e = Empleado(nombre=nombre, apellido=ap, puesto=puesto,
                     salario=Decimal(salario), telefono="55-0000-0000")
        db.session.add(e)
        empleados.append(e)
    db.session.flush()

    # --- Usuarios ---
    for nombre, user, email, pw, rol, emp_idx in USUARIOS:
        u = Usuario(nombre=nombre, username=user, email=email, rol=rol,
                    empleado_id=empleados[emp_idx].id if emp_idx is not None else None)
        u.set_password(pw)
        db.session.add(u)

    # --- Categorías y platillos ---
    platillos = []
    for orden, (cat_nombre, items) in enumerate(CATEGORIAS.items()):
        cat = Categoria(nombre=cat_nombre, orden=orden)
        db.session.add(cat)
        db.session.flush()
        for nombre, precio, minutos, img in items:
            p = Platillo(nombre=nombre, precio=Decimal(precio), tiempo_preparacion=minutos,
                         imagen_url=img, categoria_id=cat.id,
                         descripcion=f"Deliciosa preparación de la casa: {nombre.lower()}.")
            db.session.add(p)
            platillos.append(p)

    # --- Mesas ---
    for n in range(1, 13):
        db.session.add(Mesa(numero=n, capacidad=random.choice([2, 4, 4, 6, 8]),
                            ubicacion=random.choice(["Salón", "Terraza", "Barra"])))

    # --- Insumos ---
    for nombre, unidad, stock, minimo, costo in INSUMOS:
        db.session.add(Insumo(nombre=nombre, unidad=unidad,
                              stock_actual=Decimal(stock), stock_minimo=Decimal(minimo),
                              costo_unitario=Decimal(costo)))

    db.session.commit()

    # --- Historial de pedidos + facturas (últimos 30 días) ---
    admin = Usuario.query.filter_by(username="admin").first()
    cajero = Usuario.query.filter_by(username="cajero").first()
    mesero = Usuario.query.filter_by(username="mesero").first()
    mesas = Mesa.query.all()
    disponibles = Platillo.query.all()
    IVA = Decimal("0.16")
    folio = 1

    for dia in range(30, 0, -1):
        fecha = datetime.utcnow() - timedelta(days=dia)
        for _ in range(random.randint(4, 14)):
            mesa = random.choice(mesas)
            hora = fecha.replace(hour=random.randint(13, 22), minute=random.randint(0, 59))
            pedido = Pedido(mesa_id=mesa.id, usuario_id=mesero.id, estado="cobrado",
                            creado_en=hora, actualizado_en=hora)
            db.session.add(pedido)
            db.session.flush()

            subtotal = Decimal("0")
            for _ in range(random.randint(1, 5)):
                plat = random.choice(disponibles)
                qty = random.randint(1, 3)
                det = DetallePedido(pedido_id=pedido.id, platillo_id=plat.id, cantidad=qty,
                                    precio_unitario=Decimal(plat.precio), estado="entregado",
                                    creado_en=hora, listo_en=hora + timedelta(minutes=plat.tiempo_preparacion))
                db.session.add(det)
                subtotal += Decimal(plat.precio) * qty

            impuesto = (subtotal * IVA).quantize(Decimal("0.01"))
            total = subtotal + impuesto
            db.session.add(Factura(
                folio=f"F-{hora:%Y%m%d}-{folio:04d}", pedido_id=pedido.id,
                cajero_id=cajero.id, subtotal=subtotal, impuesto=impuesto, total=total,
                metodo_pago=random.choice(["efectivo", "efectivo", "tarjeta", "transferencia"]),
                pago_recibido=total, cambio=Decimal("0"), creado_en=hora))
            folio += 1

    # --- Algunos pedidos activos para el KDS de hoy ---
    for i in range(3):
        mesa = mesas[i]
        mesa.estado = "ocupada"
        ped = Pedido(mesa_id=mesa.id, usuario_id=mesero.id, estado="en_preparacion",
                     creado_en=datetime.utcnow() - timedelta(minutes=random.randint(2, 18)))
        db.session.add(ped)
        db.session.flush()
        for _ in range(random.randint(2, 4)):
            plat = random.choice(disponibles)
            db.session.add(DetallePedido(
                pedido_id=ped.id, platillo_id=plat.id, cantidad=random.randint(1, 2),
                precio_unitario=Decimal(plat.precio),
                estado=random.choice(["pendiente", "pendiente", "en_preparacion"]),
                creado_en=ped.creado_en))
    mesas[4].estado = "reservada"

    db.session.commit()
    print("Datos de demostración cargados.")
    print("  Usuarios:  admin/admin123  mesero/mesero123  cocina/cocina123  cajero/cajero123")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_seed(reset="--reset" in sys.argv)
