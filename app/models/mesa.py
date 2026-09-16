from app.extensions import db

M_LIBRE = "libre"
M_OCUPADA = "ocupada"
M_RESERVADA = "reservada"
MESA_ESTADOS = (M_LIBRE, M_OCUPADA, M_RESERVADA)

ESTADO_COLOR = {
    M_LIBRE: "success",
    M_OCUPADA: "danger",
    M_RESERVADA: "warning",
}


class Mesa(db.Model):
    __tablename__ = "mesas"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    capacidad = db.Column(db.Integer, default=4, nullable=False)
    ubicacion = db.Column(db.String(60), default="Salón")
    estado = db.Column(db.String(20), default=M_LIBRE, nullable=False)

    pedidos = db.relationship("Pedido", back_populates="mesa")

    @property
    def color(self):
        return ESTADO_COLOR.get(self.estado, "secondary")

    @property
    def pedido_activo(self):
        from app.models.pedido import Pedido, P_ABIERTO, P_EN_PREP, P_LISTO, P_SERVIDO

        return (
            Pedido.query.filter(
                Pedido.mesa_id == self.id,
                Pedido.estado.in_([P_ABIERTO, P_EN_PREP, P_LISTO, P_SERVIDO]),
            )
            .order_by(Pedido.creado_en.desc())
            .first()
        )

    def __repr__(self):
        return f"<Mesa {self.numero} ({self.estado})>"
