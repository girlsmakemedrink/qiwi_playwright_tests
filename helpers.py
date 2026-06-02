"""Вспомогательные функции: сборка тел запросов и валидация контрактов."""
from __future__ import annotations

import json
import time
from typing import Any

from jsonschema import Draft202012Validator
from playwright.sync_api import APIResponse

from config import RUB_CURRENCY_CODE_STR


def parse_json(response: APIResponse, context: str = "") -> Any:
    """Безопасный разбор тела ответа в JSON.

    Нерабочий сервис может вернуть пустое тело или HTML вместо JSON. В этом
    случае выдаём осмысленное сообщение (а не сырой ``JSONDecodeError``):
    отсутствие валидного JSON — само по себе признак неисправности сервиса.
    """
    raw = response.text()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        snippet = (raw[:200] + "…") if len(raw) > 200 else raw
        where = f" ({context})" if context else ""
        raise AssertionError(
            f"Ответ не является валидным JSON{where}. "
            f"HTTP {response.status} {response.status_text}. "
            f"Тело ответа: {snippet!r}"
        )


def generate_payment_id() -> str:
    """Уникальный идентификатор платежа (как в примерах документации — ms-таймстамп)."""
    return str(int(time.time() * 1000))


def build_p2p_payment_body(recipient_wallet: str, amount: float, comment: str = "") -> dict[str, Any]:
    """Тело запроса для перевода на QIWI Кошелёк (provider 99).

    Структура соответствует классу Payment из документации.
    """
    return {
        "id": generate_payment_id(),
        "sum": {
            "amount": amount,
            "currency": RUB_CURRENCY_CODE_STR,
        },
        "paymentMethod": {
            "type": "Account",
            "accountId": RUB_CURRENCY_CODE_STR,
        },
        "comment": comment,
        "fields": {
            "account": recipient_wallet,
        },
    }


def assert_matches_schema(payload: Any, schema: dict[str, Any], context: str = "") -> None:
    """Валидация JSON по схеме с человекочитаемым сообщением об ошибке.

    Собирает ВСЕ нарушения контракта сразу, а не падает на первом.
    """
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        details = "\n".join(
            f"  - path={'/'.join(map(str, err.path)) or '<root>'}: {err.message}"
            for err in errors
        )
        prefix = f"Ответ не соответствует документации ({context}):\n" if context else "Ответ не соответствует документации:\n"
        raise AssertionError(prefix + details)
