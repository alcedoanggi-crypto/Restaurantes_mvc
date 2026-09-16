"""Instancias de extensiones (patrón application factory)."""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    from app.models import Usuario

    return db.session.get(Usuario, int(user_id))
