from datetime import datetime
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import Empleado, Usuario
from app.security import ADMIN, ROLES, roles_required

bp = Blueprint("personal", __name__, url_prefix="/personal")


@bp.route("/")
@roles_required(ADMIN)
def index():
    return render_template(
        "personal/index.html",
        empleados=Empleado.query.order_by(Empleado.nombre).all(),
        usuarios=Usuario.query.order_by(Usuario.nombre).all(),
        roles=ROLES,
    )


# ---------- Empleados ----------
@bp.route("/empleado/guardar", methods=["POST"])
@roles_required(ADMIN)
def guardar_empleado():
    eid = request.form.get("id", type=int)
    emp = db.session.get(Empleado, eid) if eid else Empleado()
    emp.nombre = request.form.get("nombre", "").strip()
    emp.apellido = request.form.get("apellido", "").strip()
    emp.puesto = request.form.get("puesto", "Mesero").strip() or "Mesero"
    emp.telefono = request.form.get("telefono", "").strip() or None
    emp.salario = Decimal(request.form.get("salario", "0") or "0")
    fecha = request.form.get("fecha_contratacion")
    if fecha:
        try:
            emp.fecha_contratacion = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            pass
    if not emp.nombre or not emp.apellido:
        flash("Nombre y apellido son obligatorios.", "danger")
        return redirect(url_for("personal.index"))
    if not eid:
        db.session.add(emp)
    db.session.commit()
    flash("Empleado guardado.", "success")
    return redirect(url_for("personal.index"))


@bp.route("/empleado/<int:eid>/baja", methods=["POST"])
@roles_required(ADMIN)
def baja_empleado(eid):
    emp = db.session.get(Empleado, eid) or abort(404)
    emp.activo = not emp.activo
    db.session.commit()
    flash("Estado del empleado actualizado.", "info")
    return redirect(url_for("personal.index"))


# ---------- Usuarios ----------
@bp.route("/usuario/guardar", methods=["POST"])
@roles_required(ADMIN)
def guardar_usuario():
    uid = request.form.get("id", type=int)
    user = db.session.get(Usuario, uid) if uid else Usuario()

    user.nombre = request.form.get("nombre", "").strip()
    user.username = request.form.get("username", "").strip().lower()
    user.email = request.form.get("email", "").strip().lower()
    rol = request.form.get("rol")
    if rol in ROLES:
        user.rol = rol
    user.empleado_id = request.form.get("empleado_id", type=int) or None

    dup = Usuario.query.filter(
        (Usuario.username == user.username) | (Usuario.email == user.email)
    ).first()
    if dup and dup.id != user.id:
        flash("Usuario o email ya registrados.", "danger")
        return redirect(url_for("personal.index"))

    password = request.form.get("password", "")
    if not uid:
        if not password:
            flash("La contraseña es obligatoria para un usuario nuevo.", "danger")
            return redirect(url_for("personal.index"))
        user.set_password(password)
        db.session.add(user)
    elif password:
        user.set_password(password)

    if not user.nombre or not user.username or not user.email:
        flash("Nombre, usuario y email son obligatorios.", "danger")
        return redirect(url_for("personal.index"))

    db.session.commit()
    flash("Usuario guardado.", "success")
    return redirect(url_for("personal.index"))


@bp.route("/usuario/<int:uid>/activar", methods=["POST"])
@roles_required(ADMIN)
def activar_usuario(uid):
    user = db.session.get(Usuario, uid) or abort(404)
    if user.id == current_user.id:
        flash("No puedes desactivar tu propia cuenta.", "warning")
    else:
        user.activo = not user.activo
        db.session.commit()
        flash("Estado del usuario actualizado.", "info")
    return redirect(url_for("personal.index"))
