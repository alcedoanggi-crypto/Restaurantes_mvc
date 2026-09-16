"""Lógica de negocio para dashboard, reportes y cierre de caja.

Las series de tiempo se agregan en Python para no depender de funciones de
fecha específicas de PostgreSQL/SQLite.
"""
from collections import OrderedDict
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models import (
    DetallePedido,
    Factura,
    Mesa,
    MESA_ESTADOS,
    Pedido,
    Platillo,
)

CERO = Decimal("0.00")


def _rango_dia(d: date):
    inicio = datetime(d.year, d.month, d.day)
    return inicio, inicio + timedelta(days=1)


def ventas_del_dia(d: date | None = None) -> Decimal:
    d = d or date.today()
    ini, fin = _rango_dia(d)
    total = (
        db.session.query(func.coalesce(func.sum(Factura.total), 0))
        .filter(Factura.creado_en >= ini, Factura.creado_en < fin)
        .scalar()
    )
    return Decimal(total or 0)


def kpis() -> dict:
    hoy = date.today()
    ini, fin = _rango_dia(hoy)
    facturas_hoy = Factura.query.filter(
        Factura.creado_en >= ini, Factura.creado_en < fin
    ).all()

    ventas_hoy = sum((f.total for f in facturas_hoy), CERO)
    num_tickets = len(facturas_hoy)
    ticket_promedio = (ventas_hoy / num_tickets) if num_tickets else CERO

    # Mesa más rentable (histórico)
    mesa_row = (
        db.session.query(Mesa.numero, func.sum(Factura.total).label("t"))
        .join(Pedido, Pedido.mesa_id == Mesa.id)
        .join(Factura, Factura.pedido_id == Pedido.id)
        .group_by(Mesa.numero)
        .order_by(func.sum(Factura.total).desc())
        .first()
    )

    # Platillo estrella (por unidades vendidas, histórico)
    plat_row = (
        db.session.query(Platillo.nombre, func.sum(DetallePedido.cantidad).label("c"))
        .join(DetallePedido, DetallePedido.platillo_id == Platillo.id)
        .group_by(Platillo.nombre)
        .order_by(func.sum(DetallePedido.cantidad).desc())
        .first()
    )

    return {
        "ventas_hoy": ventas_hoy,
        "num_tickets": num_tickets,
        "ticket_promedio": ticket_promedio,
        "pedidos_abiertos": Pedido.query.filter(
            Pedido.estado.notin_(["cobrado", "cancelado"])
        ).count(),
        "mesa_mas_rentable": (
            {"numero": mesa_row[0], "total": Decimal(mesa_row[1] or 0)}
            if mesa_row
            else None
        ),
        "platillo_estrella": (
            {"nombre": plat_row[0], "unidades": int(plat_row[1] or 0)}
            if plat_row
            else None
        ),
    }


def platillos_mas_vendidos(limite: int = 7):
    rows = (
        db.session.query(
            Platillo.nombre, func.sum(DetallePedido.cantidad).label("c")
        )
        .join(DetallePedido, DetallePedido.platillo_id == Platillo.id)
        .group_by(Platillo.nombre)
        .order_by(func.sum(DetallePedido.cantidad).desc())
        .limit(limite)
        .all()
    )
    return {
        "labels": [r[0] for r in rows],
        "data": [int(r[1] or 0) for r in rows],
    }


def ventas_por_dia(dias: int = 14):
    hoy = date.today()
    fechas = [(hoy - timedelta(days=i)) for i in range(dias - 1, -1, -1)]
    acumulado = OrderedDict((f.isoformat(), 0.0) for f in fechas)

    desde, _ = _rango_dia(fechas[0])
    for f in Factura.query.filter(Factura.creado_en >= desde).all():
        clave = f.creado_en.date().isoformat()
        if clave in acumulado:
            acumulado[clave] += float(f.total)

    return {
        "labels": [d[5:] for d in acumulado.keys()],  # MM-DD
        "data": [round(v, 2) for v in acumulado.values()],
    }


def ventas_por_mes(meses: int = 6):
    hoy = date.today().replace(day=1)
    claves = []
    cursor = hoy
    for _ in range(meses):
        claves.append(cursor.strftime("%Y-%m"))
        # retroceder un mes
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    claves.reverse()
    acumulado = OrderedDict((k, 0.0) for k in claves)

    for f in Factura.query.all():
        k = f.creado_en.strftime("%Y-%m")
        if k in acumulado:
            acumulado[k] += float(f.total)

    return {
        "labels": list(acumulado.keys()),
        "data": [round(v, 2) for v in acumulado.values()],
    }


def ocupacion_mesas():
    counts = dict(
        db.session.query(Mesa.estado, func.count(Mesa.id)).group_by(Mesa.estado).all()
    )
    return {
        "labels": [e.capitalize() for e in MESA_ESTADOS],
        "data": [counts.get(e, 0) for e in MESA_ESTADOS],
    }


def cierre_caja(d: date | None = None):
    d = d or date.today()
    ini, fin = _rango_dia(d)
    facturas = (
        Factura.query.filter(Factura.creado_en >= ini, Factura.creado_en < fin)
        .order_by(Factura.creado_en)
        .all()
    )

    por_metodo = OrderedDict(
        (m, {"count": 0, "total": CERO}) for m in ("efectivo", "tarjeta", "transferencia")
    )
    for f in facturas:
        bucket = por_metodo.setdefault(
            f.metodo_pago, {"count": 0, "total": CERO}
        )
        bucket["count"] += 1
        bucket["total"] += f.total

    return {
        "fecha": d,
        "facturas": facturas,
        "por_metodo": por_metodo,
        "subtotal": sum((f.subtotal for f in facturas), CERO),
        "impuesto": sum((f.impuesto for f in facturas), CERO),
        "total": sum((f.total for f in facturas), CERO),
        "num_tickets": len(facturas),
    }
