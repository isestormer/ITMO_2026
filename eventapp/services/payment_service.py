"""
services/payment_service.py - платёжный шлюз.

Для дипломной работы интеграция с реальным платёжным провайдером
выходит за рамки задания и требует внешних
учётных данных и сетевого доступа. Вместо этого реализован МОК
платёжного шлюза с тем же интерфейсом (process_payment), который в
проде заменяется на настоящий вызов API провайдера без изменения
остального кода приложения.

Мок эмулирует типичное поведение платёжного шлюза:
  - генерирует уникальный номер транзакции;
  - имитирует небольшую задержку обработки;
  - может быть переведён в режим "случайных отказов" для демонстрации
    обработки ошибок оплаты (см. PAYMENT_ALWAYS_SUCCEED в config.py).
"""

import random
import string
import time


def _generate_transaction_ref():
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"MOCK-{suffix}"


def process_payment(amount, always_succeed=True, simulate_delay=False):
    """
    Обрабатывает оплату.

    @requires: amount - число >= 0.
    @effects: не производит реальных финансовых операций (мок).
    @returns: dict {"success": bool, "transaction_ref": str|None,
        "message": str}.
    """
    if simulate_delay:
        time.sleep(0.05)

    if amount <= 0:
        # Бесплатное мероприятие -- оплата не требуется, считается
        # автоматически подтверждённой без обращения к "шлюзу".
        return {
            "success": True,
            "transaction_ref": "FREE-EVENT",
            "message": "Мероприятие бесплатное, оплата не требуется.",
        }

    success = True if always_succeed else random.random() > 0.1  # 10% отказов

    if success:
        return {
            "success": True,
            "transaction_ref": _generate_transaction_ref(),
            "message": "Оплата прошла успешно.",
        }
    return {
        "success": False,
        "transaction_ref": None,
        "message": "Платёж отклонён банком-эмитентом (эмуляция отказа).",
    }
