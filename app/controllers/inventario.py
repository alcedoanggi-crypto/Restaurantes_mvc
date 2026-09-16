from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Insumo
from app.security import ADMIN, COCINA, roles_required

bp = Blueprint("inventario", __name__, url_prefix="/inventario")


@bp.route("/")
@roles_required(ADMIN, COCINA)
def index():
    insumos = Insumo.query.order_by(Insumo.nombre).all()
    valor_total = sum((i.valor_inventario for i in insumos), Decimal("0"))
    bajos = [i for i in insumos if i.bajo_stock]
    return render_template(
        "inventario/index.html", insumos=insumos, valor_total=valor_total, bajos=bajos
    )


@bp.route("/guardar", methods=["POST"])
@roles_required(ADMIN)
def guardar():
    iid = request.form.get("id", type=int)
    insumo = db.session.get(Insumo, iid) if iid else Insumo()
    insumo.nombre = request.form.get("nombre", "").strip()
    insumo.unidad = request.form.get("unidad", "pza").strip() or "pza"
    insumo.stock_actual = Decimal(request.form.get("stock_actual", "0") or "0")
    insumo.stock_minimo = Decimal(request.form.get("stock_minimo", "0") or "0")
    insumo.costo_unitario = Decimal(request.form.get("costo_unitario", "0") or "0")
    if not insumo.nombre:
        flash("El nombre es obligatorio.", "danger")
        return redirect(url_for("inventario.index"))
    if not iid:
        db.session.add(insumo)
    db.session.commit()
    flash("Insumo guardado.", "success")
    return redirect(url_for("inventario.index"))


@bp.route("/<int:iid>/ajustar", methods=["POST"])
@roles_required(ADMIN, COCINA)
def ajustar(iid):
    insumo = db.session.get(Insumo, iid) or abort(404)
    delta = Decimal(request.form.get("delta", "0") or "0")
    insumo.stock_actual = max(Decimal("0"), insumo.stock_actual + delta)
    db.session.commit()
    flash(f"Stock de {insumo.nombre}: {insumo.stock_actual} {insumo.unidad}.", "info")
    return redirect(url_for("inventario.index"))


@bp.route("/<int:iid>/eliminar", methods=["POST"])
@roles_required(ADMIN)
def eliminar(iid):
    insumo = db.session.get(Insumo, iid) or abort(404)
    db.session.delete(insumo)
    db.session.commit()
    flash("Insumo eliminado.", "info")
    return redirect(url_for("inventario.index"))
