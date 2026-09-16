from app.extensions import db


class Platillo(db.Model):
    __tablename__ = "platillos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    imagen_url = db.Column(db.String(300))
    disponible = db.Column(db.Boolean, default=True, nullable=False)
    tiempo_preparacion = db.Column(db.Integer, default=10)  # minutos estimados

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    categoria = db.relationship("Categoria", back_populates="platillos")

    detalles = db.relationship("DetallePedido", back_populates="platillo")

    @property
    def imagen(self):
        return self.imagen_url or (
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"
            "?auto=format&fit=crop&w=600&q=60"
        )

    def __repr__(self):
        return f"<Platillo {self.nombre}>"
