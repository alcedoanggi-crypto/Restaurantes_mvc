"""Endpoints JSON para gráficos (Chart.js) y refresco en tiempo real (polling)."""
from flask import Blueprint, jsonify
from flask_login import login_required

from app.models import M_LIBRE, M_OCUPADA, M_RESERVADA, Mesa
from app.security import ADMIN, CAJERO, COCINA, MESERO, roles_required
from app.services import reportes
from app.controllers.cocina import _tickets

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/dashboard/charts")
@roles_required(ADMIN, CAJERO)
def dashboard_charts():
    return jsonify(
        top_platillos=reportes.platillos_mas_vendidos(7),
        ventas_dia=reportes.ventas_por_dia(14),
        ventas_mes=reportes.ventas_por_mes(6),
        ocupacion=reportes.ocupacion_mesas(),
        kpis={k: (float(v) if hasattr(v, "__float__") else v)
              for k, v in _kpis_serializables().items()},
    )


def _kpis_serializables():
    k = reportes.kpis()
    return {
        "ventas_hoy": float(k["ventas_hoy"]),
        "num_tickets": k["num_tickets"],
        "ticket_promedio": float(k["ticket_promedio"]),
        "pedidos_abiertos": k["pedidos_abiertos"],
    }


@bp.route("/cocina")
@roles_required(ADMIN, COCINA, MESERO)
def cocina_feed():
    out = []
    for t in _tickets():
        p = t["pedido"]
        out.append(
            {
                "pedido_id": p.id,
                "mesa": p.mesa.numero,
                "mesero": p.mesero.nombre,
                "espera": t["espera"],
                "nivel": t["nivel"],
                "todo_listo": t["todo_listo"],
                "items": [
                    {
                        "id": d.id,
                        "nombre": d.platillo.nombre,
                        "cantidad": d.cantidad,
                        "estado": d.estado,
                        "notas": d.notas,
                        "minutos": d.minutos_espera,
                    }
                    for d in t["renglones"]
                ],
            }
        )
    return jsonify(tickets=out)


@bp.route("/mesas")
@login_required
def mesas_feed():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return jsonify(
        mesas=[
            {
                "id": m.id,
                "numero": m.numero,
                "estado": m.estado,
                "color": m.color,
                "pedido_id": m.pedido_activo.id if m.pedido_activo else None,
                "total": float(m.pedido_activo.subtotal) if m.pedido_activo else 0.0,
            }
            for m in mesas
        ],
        resumen={
            "libre": sum(1 for m in mesas if m.estado == M_LIBRE),
            "ocupada": sum(1 for m in mesas if m.estado == M_OCUPADA),
            "reservada": sum(1 for m in mesas if m.estado == M_RESERVADA),
        },
    )
