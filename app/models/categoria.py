from app.extensions import db


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    orden = db.Column(db.Integer, default=0)

    platillos = db.relationship(
        "Platillo", back_populates="categoria", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Categoria {self.nombre}>"
