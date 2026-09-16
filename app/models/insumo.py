from app.extensions import db


class Insumo(db.Model):
    __tablename__ = "insumos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    unidad = db.Column(db.String(20), default="pza")  # kg, lt, pza...
    stock_actual = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    stock_minimo = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    costo_unitario = db.Column(db.Numeric(10, 2), default=0)

    @property
    def bajo_stock(self):
        return self.stock_actual <= self.stock_minimo

    @property
    def valor_inventario(self):
        return (self.costo_unitario or 0) * self.stock_actual

    def __repr__(self):
        return f"<Insumo {self.nombre} {self.stock_actual}{self.unidad}>"
