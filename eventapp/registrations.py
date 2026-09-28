"""
registrations.py - регистрация участников на мероприятия ("билеты").
"""

from flask import Blueprint, abort, flash, g, redirect, render_template, url_for

from auth import login_required, role_required
from db import get_db
from services.notification_service import notify

bp = Blueprint("registrations", __name__, url_prefix="/registrations")


@bp.route("/event/<int:event_id>/register", methods=("POST",))
@role_required("participant")
def register_for_event(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if event is None:
        abort(404)
    if event["status"] != "published":
        flash("Регистрация на это мероприятие недоступна.", "danger")
        return redirect(url_for("events.detail", event_id=event_id))

    already = db.execute(
        "SELECT * FROM registrations WHERE event_id = ? AND participant_id = ? "
        "AND status != 'cancelled'",
        (event_id, g.user["id"]),
    ).fetchone()
    if already is not None:
        flash("Вы уже зарегистрированы на это мероприятие.", "warning")
        return redirect(url_for("events.detail", event_id=event_id))

    registered_count = db.execute(
        "SELECT COUNT(*) AS c FROM registrations WHERE event_id = ? AND status != 'cancelled'",
        (event_id,),
    ).fetchone()["c"]
    if registered_count >= event["capacity"]:
        flash("Свободных мест не осталось.", "danger")
        return redirect(url_for("events.detail", event_id=event_id))

    # Бесплатные мероприятия сразу подтверждаются; платные ждут оплаты.
    status = "confirmed" if event["price"] <= 0 else "pending"

    # Если участник ранее отменил регистрацию на это мероприятие, строка в
    # registrations уже существует (UNIQUE(event_id, participant_id)) 
    # повторно активируем её, а не создаём новую.
    cancelled = db.execute(
        "SELECT id FROM registrations WHERE event_id = ? AND participant_id = ? "
        "AND status = 'cancelled'",
        (event_id, g.user["id"]),
    ).fetchone()
    if cancelled is not None:
        registration_id = cancelled["id"]
        db.execute(
            "UPDATE registrations SET status = ?, registered_at = datetime('now') WHERE id = ?",
            (status, registration_id),
        )
    else:
        cur = db.execute(
            "INSERT INTO registrations (event_id, participant_id, status) VALUES (?, ?, ?)",
            (event_id, g.user["id"], status),
        )
        registration_id = cur.lastrowid

    if event["price"] > 0:
        # одна регистрация - одна актуальная оплата: сбрасываем прежнюю
        # (например, возвращённую) в состояние "ожидает оплаты"
        updated = db.execute(
            "UPDATE payments SET amount = ?, status = 'pending', "
            "transaction_ref = NULL, paid_at = NULL WHERE registration_id = ?",
            (event["price"], registration_id),
        ).rowcount
        if updated == 0:
            db.execute(
                "INSERT INTO payments (registration_id, amount, status) VALUES (?, ?, 'pending')",
                (registration_id, event["price"]),
            )
    db.commit()

    from flask import current_app
    notify(db, current_app.config, g.user, "registration_confirmation", event_row=event)

    if event["price"] > 0:
        flash("Вы зарегистрированы. Для подтверждения места необходимо оплатить участие.", "info")
        return redirect(url_for("payments.pay", registration_id=registration_id))

    flash("Вы успешно зарегистрированы на мероприятие!", "success")
    return redirect(url_for("events.detail", event_id=event_id))


@bp.route("/mine")
@login_required
def mine():
    if g.user["role"] != "participant":
        abort(403)
    db = get_db()
    rows = db.execute(
        "SELECT r.*, e.title, e.start_datetime, e.location, e.price, "
        "       p.status AS payment_status "
        "FROM registrations r "
        "JOIN events e ON e.id = r.event_id "
        "LEFT JOIN payments p ON p.registration_id = r.id "
        "WHERE r.participant_id = ? ORDER BY e.start_datetime DESC",
        (g.user["id"],),
    ).fetchall()
    return render_template("registrations/mine.html", rows=rows)


@bp.route("/<int:registration_id>/cancel", methods=("POST",))
@login_required
def cancel(registration_id):
    db = get_db()
    reg = db.execute("SELECT * FROM registrations WHERE id = ?", (registration_id,)).fetchone()
    if reg is None:
        abort(404)
    if reg["participant_id"] != g.user["id"]:
        abort(403)

    db.execute("UPDATE registrations SET status = 'cancelled' WHERE id = ?", (registration_id,))
    db.execute(
        "UPDATE payments SET status = 'refunded' WHERE registration_id = ? AND status = 'paid'",
        (registration_id,),
    )
    db.commit()
    flash("Регистрация отменена.", "info")
    return redirect(url_for("registrations.mine"))
