from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Categoria, Platillo
from app.security import ADMIN, COCINA, roles_required

bp = Blueprint("menu", __name__, url_prefix="/menu")


@bp.route("/")
@roles_required(ADMIN, COCINA)
def index():
    categorias = Categoria.query.order_by(Categoria.orden, Categoria.nombre).all()
    return render_template("menu/index.html", categorias=categorias)


# ---------- Categorías ----------
@bp.route("/categoria/crear", methods=["POST"])
@roles_required(ADMIN)
def crear_categoria():
    nombre = request.form.get("nombre", "").strip()
    if not nombre:
        flash("El nombre es obligatorio.", "danger")
    elif Categoria.query.filter_by(nombre=nombre).first():
        flash("Ya existe esa categoría.", "warning")
    else:
        db.session.add(
            Categoria(
                nombre=nombre,
                descripcion=request.form.get("descripcion", "").strip() or None,
                orden=request.form.get("orden", 0, type=int),
            )
        )
        db.session.commit()
        flash("Categoría creada.", "success")
    return redirect(url_for("menu.index"))


@bp.route("/categoria/<int:cat_id>/eliminar", methods=["POST"])
@roles_required(ADMIN)
def eliminar_categoria(cat_id):
    cat = db.session.get(Categoria, cat_id) or abort(404)
    if cat.platillos:
        flash("La categoría tiene platillos asignados.", "danger")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash("Categoría eliminada.", "info")
    return redirect(url_for("menu.index"))


# ---------- Platillos ----------
@bp.route("/platillo/guardar", methods=["POST"])
@roles_required(ADMIN)
def guardar_platillo():
    pid = request.form.get("id", type=int)
    platillo = db.session.get(Platillo, pid) if pid else Platillo()

    platillo.nombre = request.form.get("nombre", "").strip()
    platillo.descripcion = request.form.get("descripcion", "").strip() or None
    platillo.precio = Decimal(request.form.get("precio", "0") or "0")
    platillo.categoria_id = request.form.get("categoria_id", type=int)
    platillo.imagen_url = request.form.get("imagen_url", "").strip() or None
    platillo.tiempo_preparacion = request.form.get("tiempo_preparacion", 10, type=int)
    platillo.disponible = bool(request.form.get("disponible"))

    if not platillo.nombre or not platillo.categoria_id:
        flash("Nombre y categoría son obligatorios.", "danger")
        return redirect(url_for("menu.index"))

    if not pid:
        db.session.add(platillo)
    db.session.commit()
    flash("Platillo guardado.", "success")
    return redirect(url_for("menu.index"))


@bp.route("/platillo/<int:pid>/disponibilidad", methods=["POST"])
@roles_required(ADMIN, COCINA)
def toggle_disponible(pid):
    platillo = db.session.get(Platillo, pid) or abort(404)
    platillo.disponible = not platillo.disponible
    db.session.commit()
    estado = "disponible" if platillo.disponible else "agotado"
    flash(f"{platillo.nombre}: {estado}.", "info")
    return redirect(request.referrer or url_for("menu.index"))


@bp.route("/platillo/<int:pid>/eliminar", methods=["POST"])
@roles_required(ADMIN)
def eliminar_platillo(pid):
    platillo = db.session.get(Platillo, pid) or abort(404)
    if platillo.detalles:
        platillo.disponible = False
        flash("El platillo tiene historial de ventas; se marcó como no disponible.", "warning")
    else:
        db.session.delete(platillo)
        flash("Platillo eliminado.", "info")
    db.session.commit()
    return redirect(url_for("menu.index"))
