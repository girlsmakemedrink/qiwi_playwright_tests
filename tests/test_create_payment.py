"""Сценарий 3. Создание платежа на сумму 1 рубль.

POST /sinap/api/v2/terms/99/payments  (Перевод на QIWI Кошелёк, P2P)

Проверяем, что платёж на 1 ₽ корректно создаётся: успешный HTTP-статус,
ответ соответствует контракту PaymentInfo, и реквизиты в ответе совпадают
с тем, что мы отправили (сумма = 1, валюта = рубли, получатель тот же).
"""
from __future__ import annotations

import pytest
from playwright.sync_api import APIRequestContext

from config import RUB_CURRENCY_CODE, RUB_CURRENCY_CODE_STR, Settings
from helpers import assert_matches_schema, build_p2p_payment_body, parse_json
from schemas import PAYMENT_INFO_SCHEMA

PAYMENT_AMOUNT = 1


@pytest.mark.payment_create
class TestCreatePayment:
    def _create(self, api_context: APIRequestContext, settings: Settings, amount=PAYMENT_AMOUNT):
        body = build_p2p_payment_body(
            recipient_wallet=settings.recipient_wallet,
            amount=amount,
            comment="Autotest 1 RUB payment",
        )
        response = api_context.post("/sinap/api/v2/terms/99/payments", data=body)
        return response, body

    def test_create_payment_responds_with_200(self, api_context: APIRequestContext, settings: Settings):
        response, _ = self._create(api_context, settings)
        assert response.status == 200, (
            f"Создание платежа вернуло ошибку: HTTP {response.status} {response.status_text}"
        )

    @pytest.mark.contract
    def test_create_payment_matches_contract(self, api_context: APIRequestContext, settings: Settings):
        response, _ = self._create(api_context, settings)
        assert_matches_schema(parse_json(response, context="PaymentInfo"), PAYMENT_INFO_SCHEMA, context="PaymentInfo")

    def test_created_amount_is_one_rub(self, api_context: APIRequestContext, settings: Settings):
        response, _ = self._create(api_context, settings)
        body = parse_json(response, context="PaymentInfo")
        assert float(body["sum"]["amount"]) == float(PAYMENT_AMOUNT), (
            f"Сумма платежа в ответе ({body['sum']['amount']}) не равна 1 ₽"
        )
        assert str(body["sum"]["currency"]) in (RUB_CURRENCY_CODE_STR, str(RUB_CURRENCY_CODE)), (
            f"Валюта платежа должна быть рублём, получено: {body['sum']['currency']}"
        )

    def test_recipient_matches_request(self, api_context: APIRequestContext, settings: Settings):
        response, sent = self._create(api_context, settings)
        body = parse_json(response, context="PaymentInfo")
        assert body["fields"]["account"] == sent["fields"]["account"], (
            "Получатель в ответе не совпадает с отправленным в запросе"
        )

    def test_payment_has_transaction_id(self, api_context: APIRequestContext, settings: Settings):
        response, _ = self._create(api_context, settings)
        body = parse_json(response, context="PaymentInfo")
        txn_id = body.get("transaction", {}).get("id")
        assert txn_id, "В ответе отсутствует идентификатор транзакции"
