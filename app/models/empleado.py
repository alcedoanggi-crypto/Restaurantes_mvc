from datetime import date

from app.extensions import db


class Empleado(db.Model):
    __tablename__ = "empleados"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    puesto = db.Column(db.String(60), nullable=False, default="Mesero")
    telefono = db.Column(db.String(30))
    fecha_contratacion = db.Column(db.Date, default=date.today)
    salario = db.Column(db.Numeric(10, 2), default=0)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    usuario = db.relationship("Usuario", back_populates="empleado", uselist=False)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        return f"<Empleado {self.nombre_completo}>"
