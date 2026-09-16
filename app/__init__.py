"""Application factory."""
from datetime import datetime

from flask import Flask, render_template

from app.extensions import db, login_manager, migrate


def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # --- extensiones ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- modelos (para que Alembic los detecte) ---
    from app import models  # noqa: F401

    # --- blueprints (CONTROLADORES) ---
    from app.controllers.api import bp as api_bp
    from app.controllers.auth import bp as auth_bp
    from app.controllers.caja import bp as caja_bp
    from app.controllers.cocina import bp as cocina_bp
    from app.controllers.dashboard import bp as dashboard_bp
    from app.controllers.inventario import bp as inventario_bp
    from app.controllers.menu import bp as menu_bp
    from app.controllers.mesas import bp as mesas_bp
    from app.controllers.personal import bp as personal_bp
    from app.controllers.pos import bp as pos_bp

    for bp in (
        auth_bp,
        dashboard_bp,
        pos_bp,
        cocina_bp,
        mesas_bp,
        caja_bp,
        menu_bp,
        inventario_bp,
        personal_bp,
        api_bp,
    ):
        app.register_blueprint(bp)

    _register_context(app)
    _register_errors(app)
    _register_cli(app)
    return app


def _register_context(app):
    from app.security import ADMIN, CAJERO, COCINA, MESERO, ROLES_LABEL

    @app.context_processor
    def inject_globals():
        return {
            "now": datetime.utcnow(),
            "ROL_ADMIN": ADMIN,
            "ROL_MESERO": MESERO,
            "ROL_COCINA": COCINA,
            "ROL_CAJERO": CAJERO,
            "ROLES_LABEL": ROLES_LABEL,
        }

    @app.template_filter("money")
    def money(value):
        try:
            return f"${float(value):,.2f}"
        except (TypeError, ValueError):
            return "$0.00"


def _register_errors(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors.html", code=403,
                               msg="No tienes permiso para ver esta página."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors.html", code=404,
                               msg="Página no encontrada."), 404


def _register_cli(app):
    import click

    @app.cli.command("init-db")
    def init_db():
        """Crea todas las tablas."""
        db.create_all()
        click.echo("Tablas creadas.")

    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Elimina y recrea la base de datos.")
    def seed(reset):
        """Carga datos de demostración."""
        from seed import run_seed

        run_seed(reset=reset)
