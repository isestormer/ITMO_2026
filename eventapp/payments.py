"""
payments.py - оплата регистрации (использует мок платёжного шлюза
services/payment_service.py).
"""

from datetime import datetime

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from auth import login_required
from db import get_db
from services.notification_service import notify
from services.payment_service import process_payment

bp = Blueprint("payments", __name__, url_prefix="/payments")


def _get_registration_with_event(registration_id):
    db = get_db()
    row = db.execute(
        "SELECT r.*, e.title AS event_title, e.price AS event_price, "
        "       e.start_datetime, e.location, e.id AS event_id "
        "FROM registrations r JOIN events e ON e.id = r.event_id WHERE r.id = ?",
        (registration_id,),
    ).fetchone()
    if row is None:
        abort(404)
    return row


@bp.route("/<int:registration_id>", methods=("GET", "POST"))
@login_required
def pay(registration_id):
    db = get_db()
    reg = _get_registration_with_event(registration_id)
    if reg["participant_id"] != g.user["id"]:
        abort(403)

    payment = db.execute(
        "SELECT * FROM payments WHERE registration_id = ? ORDER BY id DESC LIMIT 1",
        (registration_id,),
    ).fetchone()

    if payment is not None and payment["status"] == "paid":
        flash("Эта регистрация уже оплачена.", "info")
        return redirect(url_for("registrations.mine"))

    if request.method == "POST":
        result = process_payment(
            reg["event_price"], always_succeed=current_app.config["PAYMENT_ALWAYS_SUCCEED"]
        )
        new_status = "paid" if result["success"] else "failed"
        paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if result["success"] else None
        db.execute(
            "UPDATE payments SET status=?, transaction_ref=?, paid_at=? WHERE id=?",
            (new_status, result["transaction_ref"], paid_at, payment["id"]),
        )
        if result["success"]:
            db.execute(
                "UPDATE registrations SET status = 'confirmed' WHERE id = ?",
                (registration_id,),
            )
        db.commit()

        if result["success"]:
            event_row = db.execute("SELECT * FROM events WHERE id = ?", (reg["event_id"],)).fetchone()
            notify(
                db, current_app.config, g.user, "payment_confirmation", event_row=event_row,
                amount=reg["event_price"], transaction_ref=result["transaction_ref"],
            )
            flash("Оплата прошла успешно! Место подтверждено.", "success")
            return redirect(url_for("registrations.mine"))

        flash(result["message"], "danger")

    return render_template("payments/pay.html", reg=reg, payment=payment)
