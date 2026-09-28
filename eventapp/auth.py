"""
auth.py - регистрация, вход/выход и разграничение доступа по ролям.

Аутентификация построена на подписанной сессии Flask (server-side
cookie session, secret_key из конфигурации) - отдельная библиотека
(flask-login) не требуется для объёма функционала данного приложения.
Пароли хранятся в виде хэша (werkzeug.security.generate_password_hash,
алгоритм scrypt).
"""

import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    """Перед каждым запросом подгружает текущего пользователя в g.user (или None)."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def login_required(view):
    """Декоратор: доступ только для аутентифицированных пользователей."""
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            flash("Пожалуйста, войдите в систему.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)
    return wrapped


def role_required(role):
    """Декоратор-фабрика: доступ только для пользователей с заданной ролью."""
    def decorator(view):
        @functools.wraps(view)
        @login_required
        def wrapped(**kwargs):
            if g.user["role"] != role:
                flash("Недостаточно прав для доступа к этой странице.", "danger")
                return redirect(url_for("events.catalog"))
            return view(**kwargs)
        return wrapped
    return decorator


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "participant")

        error = None
        if not full_name:
            error = "Укажите ФИО."
        elif not email or "@" not in email:
            error = "Укажите корректный email."
        elif len(password) < 6:
            error = "Пароль должен содержать не менее 6 символов."
        elif role not in ("organizer", "participant"):
            error = "Некорректная роль."

        db = get_db()
        if error is None:
            existing = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing is not None:
                error = f"Пользователь с email {email} уже зарегистрирован."

        if error is None:
            db.execute(
                "INSERT INTO users (full_name, email, phone, password_hash, role) "
                "VALUES (?, ?, ?, ?, ?)",
                (full_name, email, phone, generate_password_hash(password), role),
            )
            db.commit()
            flash("Регистрация прошла успешно. Теперь вы можете войти.", "success")
            return redirect(url_for("auth.login"))

        flash(error, "danger")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        error = None
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Неверный email или пароль."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Добро пожаловать, {user['full_name']}!", "success")
            next_url = request.args.get("next") or url_for("events.catalog")
            return redirect(next_url)

        flash(error, "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("events.catalog"))
