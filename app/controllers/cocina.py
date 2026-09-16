from datetime import datetime

from flask import Blueprint, abort, current_app, jsonify, redirect, request, render_template, url_for
from flask_login import login_required

from app.extensions import db
from app.models import (
    D_EN_PREP,
    D_LISTO,
    D_PENDIENTE,
    DetallePedido,
    P_CANCELADO,
    P_COBRADO,
    Pedido,
)
from app.security import ADMIN, COCINA, MESERO, roles_required

bp = Blueprint("cocina", __name__, url_prefix="/cocina")

_SIGUIENTE = {D_PENDIENTE: D_EN_PREP, D_EN_PREP: D_LISTO}


def _tickets():
    """Pedidos con al menos un renglón sin entregar, ordenados por antigüedad."""
    pedidos = (
        Pedido.query.filter(Pedido.estado.notin_([P_COBRADO, P_CANCELADO]))
        .order_by(Pedido.creado_en.asc())
        .all()
    )
    data = []
    warn = current_app.config["KDS_WARN_MIN"]
    late = current_app.config["KDS_LATE_MIN"]
    for p in pedidos:
        items = [d for d in p.detalles if d.estado in (D_PENDIENTE, D_EN_PREP, D_LISTO)]
        if not items:
            continue
        espera = max((d.minutos_espera for d in items), default=0)
        nivel = "ok" if espera < warn else ("warn" if espera < late else "late")
        data.append(
            {
                "pedido": p,
                "renglones": items,
                "espera": espera,
                "nivel": nivel,
                "todo_listo": all(d.estado == D_LISTO for d in items),
            }
        )
    return data


@bp.route("/")
@roles_required(ADMIN, COCINA, MESERO)
def index():
    return render_template("cocina/kds.html", tickets=_tickets())


@bp.route("/detalle/<int:detalle_id>/avanzar", methods=["POST"])
@roles_required(ADMIN, COCINA)
def avanzar(detalle_id):
    detalle = db.session.get(DetallePedido, detalle_id) or abort(404)
    nuevo = _SIGUIENTE.get(detalle.estado)
    if nuevo:
        detalle.estado = nuevo
        detalle.listo_en = datetime.utcnow() if nuevo == D_LISTO else None
        detalle.pedido.recalcular_estado()
        db.session.commit()
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(ok=True, estado=detalle.estado)
    return redirect(url_for("cocina.index"))


@bp.route("/pedido/<int:pedido_id>/listo", methods=["POST"])
@roles_required(ADMIN, COCINA)
def marcar_pedido_listo(pedido_id):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    for d in pedido.detalles:
        if d.estado in (D_PENDIENTE, D_EN_PREP):
            d.estado = D_LISTO
            d.listo_en = datetime.utcnow()
    pedido.recalcular_estado()
    db.session.commit()
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(ok=True)
    return redirect(url_for("cocina.index"))
