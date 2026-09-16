from decimal import Decimal

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.models import (
    Categoria,
    DetallePedido,
    M_LIBRE,
    M_OCUPADA,
    Mesa,
    P_ABIERTO,
    P_CANCELADO,
    P_COBRADO,
    P_SERVIDO,
    Pedido,
    Platillo,
)
from app.security import ADMIN, CAJERO, MESERO, roles_required

bp = Blueprint("pos", __name__, url_prefix="/pos")

_STAFF = (ADMIN, MESERO, CAJERO)


@bp.route("/")
@roles_required(*_STAFF)
def index():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return render_template("pos/index.html", mesas=mesas)


def _pedido_activo(mesa):
    return (
        Pedido.query.filter(
            Pedido.mesa_id == mesa.id,
            Pedido.estado.notin_([P_COBRADO, P_CANCELADO]),
        )
        .order_by(Pedido.creado_en.desc())
        .first()
    )


@bp.route("/mesa/<int:mesa_id>")
@roles_required(*_STAFF)
def mesa(mesa_id):
    mesa = db.session.get(Mesa, mesa_id) or abort(404)
    pedido = _pedido_activo(mesa)
    if pedido is None:
        pedido = Pedido(mesa_id=mesa.id, usuario_id=current_user.id, estado=P_ABIERTO)
        db.session.add(pedido)
        if mesa.estado == M_LIBRE:
            mesa.estado = M_OCUPADA
        db.session.commit()

    categorias = Categoria.query.order_by(Categoria.orden, Categoria.nombre).all()
    return render_template(
        "pos/mesa.html", mesa=mesa, pedido=pedido, categorias=categorias
    )


@bp.route("/pedido/<int:pedido_id>/agregar", methods=["POST"])
@roles_required(*_STAFF)
def agregar_item(pedido_id):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    if pedido.estado in (P_COBRADO, P_CANCELADO):
        flash("El pedido ya está cerrado.", "warning")
        return redirect(url_for("pos.mesa", mesa_id=pedido.mesa_id))

    platillo = db.session.get(Platillo, request.form.get("platillo_id", type=int))
    if not platillo or not platillo.disponible:
        flash("Platillo no disponible.", "danger")
        return redirect(url_for("pos.mesa", mesa_id=pedido.mesa_id))

    cantidad = max(1, request.form.get("cantidad", 1, type=int))
    notas = request.form.get("notas", "").strip() or None

    # Si ya existe un renglón idéntico y aún pendiente, solo suma cantidad
    existente = next(
        (
            d
            for d in pedido.detalles
            if d.platillo_id == platillo.id
            and d.estado == "pendiente"
            and (d.notas or "") == (notas or "")
        ),
        None,
    )
    if existente:
        existente.cantidad += cantidad
    else:
        db.session.add(
            DetallePedido(
                pedido_id=pedido.id,
                platillo_id=platillo.id,
                cantidad=cantidad,
                precio_unitario=Decimal(platillo.precio),
                notas=notas,
            )
        )

    if pedido.mesa.estado == M_LIBRE:
        pedido.mesa.estado = M_OCUPADA
    db.session.commit()
    flash(f"Agregado: {cantidad}× {platillo.nombre}", "success")
    return redirect(url_for("pos.mesa", mesa_id=pedido.mesa_id))


@bp.route("/detalle/<int:detalle_id>/eliminar", methods=["POST"])
@roles_required(*_STAFF)
def eliminar_item(detalle_id):
    detalle = db.session.get(DetallePedido, detalle_id) or abort(404)
    mesa_id = detalle.pedido.mesa_id
    if detalle.estado != "pendiente":
        flash("No se puede eliminar un platillo que ya está en cocina.", "warning")
    else:
        db.session.delete(detalle)
        db.session.commit()
        flash("Platillo eliminado.", "info")
    return redirect(url_for("pos.mesa", mesa_id=mesa_id))


@bp.route("/pedido/<int:pedido_id>/notas", methods=["POST"])
@roles_required(*_STAFF)
def actualizar_notas(pedido_id):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    pedido.notas = request.form.get("notas", "").strip() or None
    db.session.commit()
    return redirect(url_for("pos.mesa", mesa_id=pedido.mesa_id))


@bp.route("/pedido/<int:pedido_id>/servir", methods=["POST"])
@roles_required(*_STAFF)
def servir(pedido_id):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    for d in pedido.detalles:
        if d.estado == "listo":
            d.estado = "entregado"
    pedido.estado = P_SERVIDO
    db.session.commit()
    flash("Pedido marcado como servido.", "success")
    return redirect(url_for("pos.mesa", mesa_id=pedido.mesa_id))


@bp.route("/pedido/<int:pedido_id>/cancelar", methods=["POST"])
@roles_required(ADMIN, MESERO)
def cancelar(pedido_id):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    if any(d.estado not in ("pendiente", "entregado") for d in pedido.detalles):
        flash("Hay platillos en preparación; no se puede cancelar.", "danger")
        return redirect(url_for("pos.mesa", mesa_id=pedido.mesa_id))
    pedido.estado = P_CANCELADO
    pedido.mesa.estado = M_LIBRE
    db.session.commit()
    flash("Pedido cancelado.", "info")
    return redirect(url_for("pos.index"))
