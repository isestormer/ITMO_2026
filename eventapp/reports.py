"""
reports.py - отчёты и статистика для организатора.
"""

from flask import Blueprint, g, render_template

from auth import role_required
from db import get_db

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.route("/")
@role_required("organizer")
def dashboard():
    db = get_db()
    organizer_id = g.user["id"]

    totals = db.execute(
        "SELECT "
        "  COUNT(*) AS total_events, "
        "  SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) AS published_events, "
        "  SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) AS cancelled_events "
        "FROM events WHERE organizer_id = ?",
        (organizer_id,),
    ).fetchone()

    registrations_total = db.execute(
        "SELECT COUNT(*) AS c FROM registrations r "
        "JOIN events e ON e.id = r.event_id "
        "WHERE e.organizer_id = ? AND r.status != 'cancelled'",
        (organizer_id,),
    ).fetchone()["c"]

    revenue_total = db.execute(
        "SELECT COALESCE(SUM(p.amount), 0) AS revenue FROM payments p "
        "JOIN registrations r ON r.id = p.registration_id "
        "JOIN events e ON e.id = r.event_id "
        "WHERE e.organizer_id = ? AND p.status = 'paid'",
        (organizer_id,),
    ).fetchone()["revenue"]

    per_event = db.execute(
        "SELECT e.id, e.title, e.capacity, e.price, e.status, "
        "  (SELECT COUNT(*) FROM registrations r "
        "     WHERE r.event_id = e.id AND r.status != 'cancelled') AS registered, "
        "  (SELECT COALESCE(SUM(p.amount), 0) FROM payments p "
        "     JOIN registrations r2 ON r2.id = p.registration_id "
        "     WHERE r2.event_id = e.id AND p.status = 'paid') AS revenue "
        "FROM events e WHERE e.organizer_id = ? ORDER BY e.start_datetime DESC",
        (organizer_id,),
    ).fetchall()

    return render_template(
        "reports/dashboard.html", totals=totals,
        registrations_total=registrations_total, revenue_total=revenue_total,
        per_event=per_event,
    )
