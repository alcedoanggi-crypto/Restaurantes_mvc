from datetime import datetime
from decimal import Decimal

from app.extensions import db

D_PENDIENTE = "pendiente"
D_EN_PREP = "en_preparacion"
D_LISTO = "listo"
D_ENTREGADO = "entregado"
DETALLE_ESTADOS = (D_PENDIENTE, D_EN_PREP, D_LISTO, D_ENTREGADO)

ESTADO_LABEL = {
    D_PENDIENTE: "Pendiente",
    D_EN_PREP: "En preparación",
    D_LISTO: "Listo",
    D_ENTREGADO: "Entregado",
}


class DetallePedido(db.Model):
    __tablename__ = "detalle_pedidos"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    platillo_id = db.Column(db.Integer, db.ForeignKey("platillos.id"), nullable=False)
    cantidad = db.Column(db.Integer, default=1, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    notas = db.Column(db.String(200))
    estado = db.Column(db.String(20), default=D_PENDIENTE, nullable=False, index=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    listo_en = db.Column(db.DateTime)

    pedido = db.relationship("Pedido", back_populates="detalles")
    platillo = db.relationship("Platillo", back_populates="detalles")

    @property
    def importe(self):
        return (self.precio_unitario or Decimal("0")) * self.cantidad

    @property
    def estado_label(self):
        return ESTADO_LABEL.get(self.estado, self.estado)

    @property
    def minutos_espera(self):
        ref = self.listo_en or datetime.utcnow()
        return int((ref - self.creado_en).total_seconds() // 60)

    def __repr__(self):
        return f"<DetallePedido {self.cantidad}x platillo={self.platillo_id}>"
