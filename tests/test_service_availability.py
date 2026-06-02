"""Сценарий 1. Проверка доступности сервиса.

Подход: дёргаем метод "Получить все платежи"
(GET /payment-history/v2/persons/{wallet}/payments) и проверяем, что:
  * сервис ответил успешным HTTP-статусом 200;
  * Content-Type — application/json;
  * тело ответа соответствует контракту из документации (JSON-Schema).

Если формат отличается от документированного — это признак, что с сервисом
что-то не так (даже при HTTP 200).
"""
from __future__ import annotations

import pytest
from playwright.sync_api import APIRequestContext

from config import Settings
from helpers import assert_matches_schema, parse_json
from schemas import PAYMENT_HISTORY_SCHEMA


@pytest.mark.availability
@pytest.mark.contract
class TestServiceAvailability:
    def _get_payments(self, api_context: APIRequestContext, settings: Settings, rows: int = 10):
        return api_context.get(
            f"/payment-history/v2/persons/{settings.wallet}/payments",
            params={"rows": rows},
        )

    def test_endpoint_responds_with_200(self, api_context: APIRequestContext, settings: Settings):
        response = self._get_payments(api_context, settings)
        assert response.status == 200, (
            f"Сервис недоступен или вернул ошибку: HTTP {response.status} {response.status_text}"
        )

    def test_response_is_json(self, api_context: APIRequestContext, settings: Settings):
        response = self._get_payments(api_context, settings)
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, (
            f"Ожидался application/json, получено: {content_type!r}"
        )

    def test_response_matches_documented_contract(
        self, api_context: APIRequestContext, settings: Settings
    ):
        response = self._get_payments(api_context, settings)
        body = parse_json(response, context="payment-history")
        assert_matches_schema(body, PAYMENT_HISTORY_SCHEMA, context="payment-history")

    def test_data_is_a_list(self, api_context: APIRequestContext, settings: Settings):
        body = parse_json(self._get_payments(api_context, settings), context="payment-history")
        assert isinstance(body.get("data"), list), "Поле 'data' должно быть массивом платежей"

    @pytest.mark.parametrize("rows", [1, 50])
    def test_respects_rows_limit(self, api_context: APIRequestContext, settings: Settings, rows: int):
        body = parse_json(self._get_payments(api_context, settings, rows=rows), context="payment-history")
        assert len(body["data"]) <= rows, (
            f"Число платежей в ответе ({len(body['data'])}) превышает запрошенный лимит rows={rows}"
        )
