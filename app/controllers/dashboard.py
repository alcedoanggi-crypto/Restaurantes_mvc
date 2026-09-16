from flask import Blueprint, render_template
from flask_login import login_required

from app.security import ADMIN, CAJERO, roles_required
from app.services import reportes

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@bp.route("/dashboard")
@login_required
def index():
    from flask_login import current_user

    # Meseros y cocina van directo a su pantalla operativa
    if current_user.rol == "mesero":
        from flask import redirect, url_for

        return redirect(url_for("pos.index"))
    if current_user.rol == "cocina":
        from flask import redirect, url_for

        return redirect(url_for("cocina.index"))

    return render_template(
        "dashboard/index.html",
        kpis=reportes.kpis(),
    )


@bp.route("/reportes")
@roles_required(ADMIN, CAJERO)
def reportes_view():
    return render_template(
        "dashboard/reportes.html",
        top=reportes.platillos_mas_vendidos(10),
        dia=reportes.ventas_por_dia(30),
        mes=reportes.ventas_por_mes(12),
    )
