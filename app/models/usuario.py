from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.security import ADMIN, ROLES_LABEL


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(60), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default=ADMIN)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=True)
    empleado = db.relationship("Empleado", back_populates="usuario")

    pedidos = db.relationship("Pedido", back_populates="mesero")
    facturas = db.relationship("Factura", back_populates="cajero")

    # --- password helpers ---
    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    @property
    def is_active(self):  # usado por Flask-Login
        return self.activo

    @property
    def rol_label(self):
        return ROLES_LABEL.get(self.rol, self.rol.title())

    def __repr__(self):
        return f"<Usuario {self.username} ({self.rol})>"
