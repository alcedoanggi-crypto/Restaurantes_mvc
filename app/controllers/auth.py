from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import Usuario

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        ident = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = Usuario.query.filter(
            (Usuario.username == ident) | (Usuario.email == ident)
        ).first()

        if user and user.check_password(password):
            if not user.activo:
                flash("Tu cuenta está desactivada. Contacta al administrador.", "danger")
                return render_template("auth/login.html")
            login_user(user, remember=bool(request.form.get("remember")))
            flash(f"¡Bienvenido, {user.nombre}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Usuario o contraseña incorrectos.", "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))
