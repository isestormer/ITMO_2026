"""
events.py - каталог мероприятий и управление мероприятиями организатором.
"""

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from auth import role_required
from db import get_db
from services.notification_service import notify

bp = Blueprint("events", __name__, url_prefix="/events")

CATEGORIES = ["Конференция", "Мастер-класс", "Концерт", "Спорт", "Выставка", "Другое"]


def _get_event_or_404(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if event is None:
        abort(404)
    return event


@bp.route("/")
def catalog():
    """Публичный каталог опубликованных мероприятий с поиском и фильтрами."""
    db = get_db()
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "")

    sql = (
        "SELECT e.*, u.full_name AS organizer_name, "
        "  (SELECT COUNT(*) FROM registrations r "
        "     WHERE r.event_id = e.id AND r.status != 'cancelled') AS registered_count "
        "FROM events e JOIN users u ON u.id = e.organizer_id "
        "WHERE e.status = 'published'"
    )
    params = []
    if query:
        sql += " AND (e.title LIKE ? OR e.description LIKE ?)"
        params += [f"%{query}%", f"%{query}%"]
    if category:
        sql += " AND e.category = ?"
        params.append(category)
    sql += " ORDER BY e.start_datetime ASC"

    events = db.execute(sql, params).fetchall()
    return render_template(
        "events/catalog.html", events=events, categories=CATEGORIES,
        query=query, category=category,
    )


@bp.route("/<int:event_id>")
def detail(event_id):
    db = get_db()
    event = _get_event_or_404(event_id)
    organizer = db.execute("SELECT * FROM users WHERE id = ?", (event["organizer_id"],)).fetchone()

    registered_count = db.execute(
        "SELECT COUNT(*) AS c FROM registrations WHERE event_id = ? AND status != 'cancelled'",
        (event_id,),
    ).fetchone()["c"]

    my_registration = None
    if g.user is not None:
        my_registration = db.execute(
            "SELECT * FROM registrations WHERE event_id = ? AND participant_id = ? "
            "AND status != 'cancelled'",
            (event_id, g.user["id"]),
        ).fetchone()

    return render_template(
        "events/detail.html", event=event, organizer=organizer,
        registered_count=registered_count, my_registration=my_registration,
    )


@bp.route("/new", methods=("GET", "POST"))
@role_required("organizer")
def create():
    if request.method == "POST":
        error, data = _validate_event_form(request.form)
        if error is None:
            db = get_db()
            db.execute(
                "INSERT INTO events (organizer_id, title, description, category, "
                " location, start_datetime, end_datetime, capacity, price, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    g.user["id"], data["title"], data["description"], data["category"],
                    data["location"], data["start"], data["end"], data["capacity"],
                    data["price"], data["status"],
                ),
            )
            db.commit()
            flash("Мероприятие создано.", "success")
            return redirect(url_for("events.my_events"))
        flash(error, "danger")

    return render_template("events/form.html", event=None, categories=CATEGORIES)


@bp.route("/<int:event_id>/edit", methods=("GET", "POST"))
@role_required("organizer")
def edit(event_id):
    event = _get_event_or_404(event_id)
    if event["organizer_id"] != g.user["id"]:
        abort(403)

    if request.method == "POST":
        error, data = _validate_event_form(request.form)
        if error is None:
            db = get_db()
            db.execute(
                "UPDATE events SET title=?, description=?, category=?, location=?, "
                "start_datetime=?, end_datetime=?, capacity=?, price=?, status=? WHERE id=?",
                (
                    data["title"], data["description"], data["category"], data["location"],
                    data["start"], data["end"], data["capacity"], data["price"],
                    data["status"], event_id,
                ),
            )
            db.commit()

            if data["status"] == "cancelled" and event["status"] != "cancelled":
                _notify_all_participants_cancelled(event_id)

            flash("Мероприятие обновлено.", "success")
            return redirect(url_for("events.my_events"))
        flash(error, "danger")

    return render_template("events/form.html", event=event, categories=CATEGORIES)


@bp.route("/mine")
@role_required("organizer")
def my_events():
    db = get_db()
    events = db.execute(
        "SELECT e.*, "
        "  (SELECT COUNT(*) FROM registrations r "
        "     WHERE r.event_id = e.id AND r.status != 'cancelled') AS registered_count "
        "FROM events e WHERE e.organizer_id = ? ORDER BY e.start_datetime DESC",
        (g.user["id"],),
    ).fetchall()
    return render_template("events/my_events.html", events=events)


@bp.route("/<int:event_id>/participants")
@role_required("organizer")
def participants(event_id):
    event = _get_event_or_404(event_id)
    if event["organizer_id"] != g.user["id"]:
        abort(403)

    db = get_db()
    rows = db.execute(
        "SELECT r.id AS reg_id, r.status AS reg_status, r.registered_at, "
        "       u.full_name, u.email, u.phone, "
        "       p.status AS payment_status, p.amount, p.transaction_ref "
        "FROM registrations r "
        "JOIN users u ON u.id = r.participant_id "
        "LEFT JOIN payments p ON p.registration_id = r.id "
        "WHERE r.event_id = ? ORDER BY r.registered_at ASC",
        (event_id,),
    ).fetchall()
    return render_template("events/participants.html", event=event, rows=rows)


def _validate_event_form(form):
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    category = form.get("category", "Другое")
    location = form.get("location", "").strip()
    start = form.get("start_datetime", "").strip()
    end = form.get("end_datetime", "").strip()
    status = form.get("status", "published")
    capacity_raw = form.get("capacity", "")
    price_raw = form.get("price", "0")

    if not title:
        return "Укажите название мероприятия.", None
    if not location:
        return "Укажите место проведения.", None
    if not start:
        return "Укажите дату и время начала.", None
    if status not in ("draft", "published", "cancelled", "completed"):
        return "Некорректный статус.", None
    try:
        capacity = int(capacity_raw)
        if capacity <= 0:
            raise ValueError
    except ValueError:
        return "Вместимость должна быть положительным целым числом.", None
    try:
        price = float(price_raw)
        if price < 0:
            raise ValueError
    except ValueError:
        return "Цена должна быть неотрицательным числом.", None

    data = {
        "title": title, "description": description, "category": category,
        "location": location, "start": start, "end": end or None,
        "capacity": capacity, "price": price, "status": status,
    }
    return None, data


def _notify_all_participants_cancelled(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    participants_rows = db.execute(
        "SELECT u.* FROM registrations r JOIN users u ON u.id = r.participant_id "
        "WHERE r.event_id = ? AND r.status != 'cancelled'",
        (event_id,),
    ).fetchall()
    from flask import current_app
    for user_row in participants_rows:
        notify(db, current_app.config, user_row, "event_cancelled", event_row=event)
