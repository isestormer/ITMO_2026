"""
tests/test_app.py - функциональные тесты Flask-приложения через тестовый клиент.

Каждый тест использует собственный временный файл SQLite.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import Config


class ExtendedTestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    EMAIL_BACKEND = "console"
    PAYMENT_ALWAYS_SUCCEED = True


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, db_path = tempfile.mkstemp(suffix=".sqlite3")
        email_fd, email_log_path = tempfile.mkstemp(suffix=".log")
        os.close(email_fd)

        class TestConf(ExtendedTestConfig):
            DATABASE_PATH = db_path
            EMAIL_LOG_PATH = email_log_path
            SECRET_KEY = "test-secret"

        self.app = create_app(TestConf)
        self.app.testing = True
        self.client = self.app.test_client()
        self.db_path = db_path
        self.email_log_path = email_log_path

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        if os.path.exists(self.email_log_path):
            os.unlink(self.email_log_path)

    # ---- вспомогательные методы -------------------------------------
    def register(self, email, password="password1", role="participant", name="Тест Тестов"):
        return self.client.post("/auth/register", data={
            "full_name": name, "email": email, "phone": "+79990000000",
            "password": password, "role": role,
        }, follow_redirects=True)

    def login(self, email, password="password1"):
        return self.client.post("/auth/login", data={
            "email": email, "password": password,
        }, follow_redirects=True)

    def create_event(self, title="Тестовая конференция", price=0, capacity=2):
        return self.client.post("/events/new", data={
            "title": title, "description": "Описание", "category": "Конференция",
            "location": "Санкт-Петербург", "start_datetime": "2026-09-01 10:00",
            "end_datetime": "2026-09-01 18:00", "capacity": str(capacity),
            "price": str(price), "status": "published",
        }, follow_redirects=True)


class TestAuth(BaseTestCase):
    def test_register_and_login(self):
        r = self.register("user1@example.com")
        self.assertEqual(r.status_code, 200)
        r = self.login("user1@example.com")
        self.assertIn("Мои регистрации".encode("utf-8"), r.data)

    def test_duplicate_email_rejected(self):
        self.register("dup@example.com")
        r = self.register("dup@example.com")
        self.assertIn("уже зарегистрирован".encode("utf-8"), r.data)

    def test_wrong_password_rejected(self):
        self.register("user2@example.com")
        r = self.login("user2@example.com", password="wrongpass")
        self.assertIn("Неверный email или пароль".encode("utf-8"), r.data)

    def test_short_password_rejected(self):
        r = self.register("user3@example.com", password="123")
        self.assertIn("не менее 6 символов".encode("utf-8"), r.data)


class TestEventsAndRegistrationFreeEvent(BaseTestCase):
    def test_organizer_can_create_event_and_participant_can_register(self):
        self.register("org1@example.com", role="organizer", name="Организатор Иванов")
        self.login("org1@example.com")
        r = self.create_event(title="Бесплатный митап", price=0, capacity=1)
        self.assertIn("Бесплатный митап".encode("utf-8"), r.data)
        self.client.get("/auth/logout")

        self.register("part1@example.com", role="participant", name="Участник Петров")
        self.login("part1@example.com")

        # найдём id мероприятия через каталог
        db = self._get_db_row("SELECT id FROM events WHERE title = ?", ("Бесплатный митап",))
        event_id = db["id"]

        r = self.client.post(f"/registrations/event/{event_id}/register", follow_redirects=True)
        self.assertIn("успешно зарегистрированы".encode("utf-8"), r.data)

        reg = self._get_db_row(
            "SELECT status FROM registrations WHERE event_id=?", (event_id,)
        )
        self.assertEqual(reg["status"], "confirmed")

    def test_registration_blocked_when_full(self):
        self.register("org2@example.com", role="organizer")
        self.login("org2@example.com")
        self.create_event(title="Маленький зал", price=0, capacity=1)
        self.client.get("/auth/logout")

        self.register("p_a@example.com", role="participant")
        self.login("p_a@example.com")
        event_id = self._get_db_row("SELECT id FROM events WHERE title=?", ("Маленький зал",))["id"]
        self.client.post(f"/registrations/event/{event_id}/register", follow_redirects=True)
        self.client.get("/auth/logout")

        self.register("p_b@example.com", role="participant")
        self.login("p_b@example.com")
        r = self.client.post(f"/registrations/event/{event_id}/register", follow_redirects=True)
        self.assertIn("Свободных мест не осталось".encode("utf-8"), r.data)

    def test_non_organizer_cannot_create_event(self):
        self.register("justparticipant@example.com", role="participant")
        self.login("justparticipant@example.com")
        r = self.client.get("/events/new", follow_redirects=True)
        self.assertIn("Недостаточно прав".encode("utf-8"), r.data)

    def _get_db_row(self, sql, params):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row


class TestPaidEventAndPayment(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.register("org3@example.com", role="organizer")
        self.login("org3@example.com")
        self.create_event(title="Платный концерт", price=500, capacity=5)
        self.client.get("/auth/logout")
        self.register("payer@example.com", role="participant")
        self.login("payer@example.com")

    def _event_id(self):
        return self._get_db_row("SELECT id FROM events WHERE title=?", ("Платный концерт",))["id"]

    def _get_db_row(self, sql, params):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row

    def test_paid_registration_starts_pending_and_payment_confirms_it(self):
        event_id = self._event_id()
        r = self.client.post(f"/registrations/event/{event_id}/register", follow_redirects=True)
        self.assertIn("оплатить участие".encode("utf-8"), r.data)

        reg = self._get_db_row("SELECT id, status FROM registrations WHERE event_id=?", (event_id,))
        self.assertEqual(reg["status"], "pending")

        payment = self._get_db_row("SELECT status FROM payments WHERE registration_id=?", (reg["id"],))
        self.assertEqual(payment["status"], "pending")

        r = self.client.post(f"/payments/{reg['id']}", follow_redirects=True)
        self.assertIn("Оплата прошла успешно".encode("utf-8"), r.data)

        reg_after = self._get_db_row("SELECT status FROM registrations WHERE id=?", (reg["id"],))
        self.assertEqual(reg_after["status"], "confirmed")
        payment_after = self._get_db_row("SELECT status, transaction_ref FROM payments WHERE registration_id=?", (reg["id"],))
        self.assertEqual(payment_after["status"], "paid")
        self.assertTrue(payment_after["transaction_ref"].startswith("MOCK-"))

    def test_email_notifications_logged(self):
        event_id = self._event_id()
        self.client.post(f"/registrations/event/{event_id}/register", follow_redirects=True)
        with open(self.email_log_path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Подтверждение регистрации", content)


class TestReRegistrationAfterCancel(BaseTestCase):
    def _row(self, sql, params=()):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row

    def test_can_register_again_after_cancel_free_and_paid(self):
        self.register("orgR@example.com", role="organizer")
        self.login("orgR@example.com")
        self.create_event(title="Бесплатное", price=0, capacity=5)
        self.create_event(title="Платное", price=300, capacity=5)
        self.client.get("/auth/logout")

        self.register("guestR@example.com", role="participant")
        self.login("guestR@example.com")

        for title, expected_first, expected_again in (
            ("Бесплатное", "confirmed", "confirmed"),
            ("Платное", "pending", "pending"),
        ):
            event_id = self._row("SELECT id FROM events WHERE title=?", (title,))["id"]
            self.client.post(f"/registrations/event/{event_id}/register", follow_redirects=True)
            reg = self._row("SELECT id, status FROM registrations WHERE event_id=?", (event_id,))
            self.assertEqual(reg["status"], expected_first)

            self.client.post(f"/registrations/{reg['id']}/cancel", follow_redirects=True)
            self.assertEqual(
                self._row("SELECT status FROM registrations WHERE id=?", (reg["id"],))["status"],
                "cancelled",
            )

            # повторная регистрация не должна падать с ошибкой 500
            r = self.client.post(f"/registrations/event/{event_id}/register", follow_redirects=True)
            self.assertEqual(r.status_code, 200)
            again = self._row("SELECT id, status FROM registrations WHERE event_id=?", (event_id,))
            self.assertEqual(again["id"], reg["id"])  # та же строка реактивирована
            self.assertEqual(again["status"], expected_again)

        # у платного мероприятия оплата снова "ожидает оплаты"
        paid_event = self._row("SELECT id FROM events WHERE title=?", ("Платное",))["id"]
        pay = self._row(
            "SELECT p.status FROM payments p JOIN registrations r ON r.id=p.registration_id "
            "WHERE r.event_id=?", (paid_event,))
        self.assertEqual(pay["status"], "pending")


class TestReports(BaseTestCase):
    def test_dashboard_shows_totals(self):
        self.register("org4@example.com", role="organizer")
        self.login("org4@example.com")
        self.create_event(title="Отчётное мероприятие", price=100, capacity=10)
        r = self.client.get("/reports/", follow_redirects=True)
        self.assertIn("Отчёты и статистика".encode("utf-8"), r.data)
        self.assertIn("Отчётное мероприятие".encode("utf-8"), r.data)


if __name__ == "__main__":
    unittest.main()
