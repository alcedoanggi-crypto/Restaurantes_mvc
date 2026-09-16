from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from app.extensions import db
from app.models import (
    Factura,
    M_LIBRE,
    METODOS_PAGO,
    P_CANCELADO,
    P_COBRADO,
    Pedido,
)
from app.security import ADMIN, CAJERO, roles_required
from app.services import reportes

bp = Blueprint("caja", __name__, url_prefix="/caja")

Q = Decimal("0.01")


def _cuantiza(v):
    return Decimal(v).quantize(Q, rounding=ROUND_HALF_UP)


@bp.route("/")
@roles_required(ADMIN, CAJERO)
def index():
    pendientes = (
        Pedido.query.filter(Pedido.estado.notin_([P_COBRADO, P_CANCELADO]))
        .order_by(Pedido.creado_en)
        .all()
    )
    pendientes = [p for p in pendientes if p.detalles]
    return render_template(
        "caja/index.html", pendientes=pendientes, resumen=reportes.cierre_caja()
    )


@bp.route("/cobrar/<int:pedido_id>", methods=["GET", "POST"])
@roles_required(ADMIN, CAJERO)
def cobrar(pedido_id):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    if pedido.estado == P_COBRADO:
        flash("Ese pedido ya fue cobrado.", "warning")
        return redirect(url_for("caja.index"))

    iva = Decimal(str(current_app.config["IVA"]))
    subtotal = _cuantiza(pedido.subtotal)
    impuesto = _cuantiza(subtotal * iva)
    total = _cuantiza(subtotal + impuesto)

    if request.method == "POST":
        metodo = request.form.get("metodo_pago", "efectivo")
        if metodo not in METODOS_PAGO:
            metodo = "efectivo"
        recibido = _cuantiza(request.form.get("pago_recibido", total, type=float) or total)
        if metodo == "efectivo" and recibido < total:
            flash("El pago recibido es menor al total.", "danger")
            return redirect(url_for("caja.cobrar", pedido_id=pedido.id))

        folio = f"F-{datetime.utcnow():%Y%m%d}-{(Factura.query.count() + 1):04d}"
        factura = Factura(
            folio=folio,
            pedido_id=pedido.id,
            cajero_id=current_user.id,
            subtotal=subtotal,
            impuesto=impuesto,
            total=total,
            metodo_pago=metodo,
            pago_recibido=recibido,
            cambio=_cuantiza(max(Decimal("0"), recibido - total)),
        )
        pedido.estado = P_COBRADO
        pedido.mesa.estado = M_LIBRE
        db.session.add(factura)
        db.session.commit()
        flash(f"Cobro registrado. Folio {folio}.", "success")
        return redirect(url_for("caja.ticket", factura_id=factura.id))

    return render_template(
        "caja/cobrar.html",
        pedido=pedido,
        subtotal=subtotal,
        impuesto=impuesto,
        total=total,
        iva=iva,
        metodos=METODOS_PAGO,
    )


@bp.route("/ticket/<int:factura_id>")
@roles_required(ADMIN, CAJERO)
def ticket(factura_id):
    factura = db.session.get(Factura, factura_id) or abort(404)
    return render_template("caja/ticket.html", f=factura)


@bp.route("/cierre")
@roles_required(ADMIN, CAJERO)
def cierre():
    fecha_str = request.args.get("fecha")
    try:
        d = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else date.today()
    except ValueError:
        d = date.today()
    return render_template("caja/cierre.html", r=reportes.cierre_caja(d))
