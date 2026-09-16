from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import MESA_ESTADOS, M_LIBRE, Mesa
from app.security import ADMIN, CAJERO, MESERO, roles_required

bp = Blueprint("mesas", __name__, url_prefix="/mesas")


@bp.route("/")
@roles_required(ADMIN, MESERO, CAJERO)
def index():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return render_template("mesas/index.html", mesas=mesas, estados=MESA_ESTADOS)


@bp.route("/crear", methods=["POST"])
@roles_required(ADMIN)
def crear():
    numero = request.form.get("numero", type=int)
    if not numero or Mesa.query.filter_by(numero=numero).first():
        flash("Número de mesa inválido o duplicado.", "danger")
        return redirect(url_for("mesas.index"))
    db.session.add(
        Mesa(
            numero=numero,
            capacidad=request.form.get("capacidad", 4, type=int),
            ubicacion=request.form.get("ubicacion", "Salón").strip() or "Salón",
        )
    )
    db.session.commit()
    flash(f"Mesa {numero} creada.", "success")
    return redirect(url_for("mesas.index"))


@bp.route("/<int:mesa_id>/editar", methods=["POST"])
@roles_required(ADMIN)
def editar(mesa_id):
    mesa = db.session.get(Mesa, mesa_id) or abort(404)
    mesa.capacidad = request.form.get("capacidad", mesa.capacidad, type=int)
    mesa.ubicacion = request.form.get("ubicacion", mesa.ubicacion).strip() or mesa.ubicacion
    db.session.commit()
    flash("Mesa actualizada.", "success")
    return redirect(url_for("mesas.index"))


@bp.route("/<int:mesa_id>/estado", methods=["POST"])
@roles_required(ADMIN, MESERO, CAJERO)
def cambiar_estado(mesa_id):
    mesa = db.session.get(Mesa, mesa_id) or abort(404)
    nuevo = request.form.get("estado")
    if nuevo in MESA_ESTADOS:
        if mesa.pedido_activo and nuevo == M_LIBRE:
            flash("La mesa tiene un pedido activo.", "warning")
        else:
            mesa.estado = nuevo
            db.session.commit()
            flash(f"Mesa {mesa.numero}: {nuevo}.", "info")
    return redirect(request.referrer or url_for("mesas.index"))


@bp.route("/<int:mesa_id>/eliminar", methods=["POST"])
@roles_required(ADMIN)
def eliminar(mesa_id):
    mesa = db.session.get(Mesa, mesa_id) or abort(404)
    if mesa.pedidos:
        flash("No se puede eliminar una mesa con historial de pedidos.", "danger")
    else:
        db.session.delete(mesa)
        db.session.commit()
        flash("Mesa eliminada.", "info")
    return redirect(url_for("mesas.index"))
