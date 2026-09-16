from datetime import datetime

from app.extensions import db

METODOS_PAGO = ("efectivo", "tarjeta", "transferencia")


class Factura(db.Model):
    __tablename__ = "facturas"

    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(20), unique=True, nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    cajero_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    impuesto = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    metodo_pago = db.Column(db.String(20), default="efectivo", nullable=False)
    pago_recibido = db.Column(db.Numeric(10, 2), default=0)
    cambio = db.Column(db.Numeric(10, 2), default=0)

    creado_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    pedido = db.relationship("Pedido", back_populates="factura")
    cajero = db.relationship("Usuario", back_populates="facturas")

    def __repr__(self):
        return f"<Factura {self.folio} total={self.total}>"
