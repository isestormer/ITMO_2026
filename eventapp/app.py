"""
app.py - фабрика Flask-приложения "Система создания и управления
мероприятиями". Регистрирует блюпринты, БД и общие обработчики ошибок.
"""

from flask import Flask, g, render_template

from config import Config
import db as db_module


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db_module.register_db(app)
    db_module.init_db(app)

    import auth
    import events
    import registrations
    import payments
    import reports

    app.register_blueprint(auth.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(registrations.bp)
    app.register_blueprint(payments.bp)
    app.register_blueprint(reports.bp)

    app.add_url_rule("/", endpoint="index")
    app.view_functions["index"] = lambda: events.catalog()

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/error.html", code=403, message="Доступ запрещён"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/error.html", code=404, message="Страница не найдена"), 404

    @app.context_processor
    def inject_user():
        return {"current_user": g.get("user")}

    return app
