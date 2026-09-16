"""Control de acceso por roles."""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user

# Roles del sistema
ADMIN = "administrador"
MESERO = "mesero"
COCINA = "cocina"
CAJERO = "cajero"
ROLES = (ADMIN, MESERO, COCINA, CAJERO)

ROLES_LABEL = {
    ADMIN: "Administrador",
    MESERO: "Mesero",
    COCINA: "Cocina",
    CAJERO: "Cajero",
}


def roles_required(*roles):
    """Restringe una vista a los roles indicados (el admin siempre pasa)."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.rol != ADMIN and current_user.rol not in roles:
                flash("No tienes permiso para acceder a esa sección.", "danger")
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
