from datetime import datetime
from decimal import Decimal

from app.extensions import db

P_ABIERTO = "abierto"
P_EN_PREP = "en_preparacion"
P_LISTO = "listo"
P_SERVIDO = "servido"
P_COBRADO = "cobrado"
P_CANCELADO = "cancelado"
PEDIDO_ESTADOS = (P_ABIERTO, P_EN_PREP, P_LISTO, P_SERVIDO, P_COBRADO, P_CANCELADO)

ESTADO_LABEL = {
    P_ABIERTO: "Abierto",
    P_EN_PREP: "En preparación",
    P_LISTO: "Listo",
    P_SERVIDO: "Servido",
    P_COBRADO: "Cobrado",
    P_CANCELADO: "Cancelado",
}


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    estado = db.Column(db.String(20), default=P_ABIERTO, nullable=False, index=True)
    notas = db.Column(db.String(255))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    actualizado_en = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    mesa = db.relationship("Mesa", back_populates="pedidos")
    mesero = db.relationship("Usuario", back_populates="pedidos")
    detalles = db.relationship(
        "DetallePedido", back_populates="pedido", cascade="all, delete-orphan"
    )
    factura = db.relationship(
        "Factura", back_populates="pedido", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def estado_label(self):
        return ESTADO_LABEL.get(self.estado, self.estado)

    @property
    def subtotal(self):
        return sum((d.importe for d in self.detalles), Decimal("0.00"))

    @property
    def total_items(self):
        return sum(d.cantidad for d in self.detalles)

    def recalcular_estado(self):
        """Ajusta el estado del pedido según el estado de sus renglones."""
        from app.models.detalle_pedido import D_EN_PREP, D_LISTO, D_PENDIENTE

        if self.estado in (P_COBRADO, P_CANCELADO, P_SERVIDO):
            return
        estados = {d.estado for d in self.detalles}
        if not estados or estados == {D_PENDIENTE}:
            self.estado = P_ABIERTO
        elif estados <= {D_LISTO}:
            self.estado = P_LISTO
        elif D_EN_PREP in estados or D_PENDIENTE in estados:
            self.estado = P_EN_PREP

    def __repr__(self):
        return f"<Pedido #{self.id} mesa={self.mesa_id} {self.estado}>"
