"""Общие фикстуры для тестов QIWI API на Playwright (Python).

Тесты используют Playwright ``APIRequestContext`` — это полноценный HTTP-клиент
Playwright для API-тестов (без запуска браузера).
"""
from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config import Settings, load_settings
from helpers import build_p2p_payment_body, parse_json


@pytest.fixture(scope="session")
def settings() -> Settings:
    return load_settings()


@pytest.fixture(scope="session")
def api_context(playwright: Playwright, settings: Settings) -> Generator[APIRequestContext, None, None]:
    """Сессионный HTTP-клиент с базовым URL и заголовком авторизации."""
    request_context = playwright.request.new_context(
        base_url=settings.base_url,
        extra_http_headers=settings.auth_headers,
        # Сервис нерабочий — не ждём ответа бесконечно.
        timeout=15_000,
    )
    yield request_context
    request_context.dispose()


@pytest.fixture
def created_payment(api_context: APIRequestContext, settings: Settings) -> dict[str, Any]:
    """Создаёт платёж на 1 рубль и возвращает разобранный JSON-ответ (PaymentInfo).

    Используется тестом исполнения платежа: чтобы проверить исполнение,
    сначала нужно успешно создать платёж.
    """
    body = build_p2p_payment_body(
        recipient_wallet=settings.recipient_wallet,
        amount=1,
        comment="Autotest 1 RUB payment",
    )
    response = api_context.post(
        f"/sinap/api/v2/terms/99/payments",
        data=body,
    )
    assert response.ok, (
        f"Не удалось создать платёж для проверки исполнения: "
        f"HTTP {response.status} {response.status_text}"
    )
    return parse_json(response, context="PaymentInfo (created_payment)")
