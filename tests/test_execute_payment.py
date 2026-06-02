"""Сценарий 4. Исполнение созданного платежа.

В QIWI создание P2P-платежа сразу принимает его к исполнению: в ответе на
создание приходит transaction.state.code == "Accepted". Поэтому проверка
исполнения состоит из двух шагов:

  1. Платёж создан и принят к исполнению (state.code == "Accepted").
  2. По идентификатору транзакции статус подтверждается как исполненный
     (GET /payment-history/v2/transactions/{id} -> status == "SUCCESS").

Фикстура ``created_payment`` создаёт платёж на 1 ₽ (см. conftest.py).
"""
from __future__ import annotations

import pytest
from playwright.sync_api import APIRequestContext

from config import Settings
from helpers import assert_matches_schema, parse_json
from schemas import TRANSACTION_SCHEMA

ACCEPTED_STATES = {"Accepted"}
EXECUTED_STATUSES = {"SUCCESS"}
TERMINAL_ERROR_STATUSES = {"ERROR"}


@pytest.mark.payment_execute
class TestExecutePayment:
    def test_payment_accepted_for_execution(self, created_payment: dict):
        """Шаг 1: созданный платёж принят к исполнению."""
        state = created_payment.get("transaction", {}).get("state", {})
        assert state.get("code") in ACCEPTED_STATES, (
            f"Платёж не принят к исполнению. transaction.state.code = {state.get('code')!r}, "
            f"ожидалось одно из {ACCEPTED_STATES}"
        )

    def test_transaction_status_is_executed(
        self, api_context: APIRequestContext, settings: Settings, created_payment: dict
    ):
        """Шаг 2: статус транзакции подтверждает исполнение (SUCCESS)."""
        txn_id = created_payment["transaction"]["id"]

        response = api_context.get(
            f"/payment-history/v2/transactions/{txn_id}",
            params={"type": "OUT"},
        )
        assert response.status == 200, (
            f"Не удалось получить статус транзакции {txn_id}: "
            f"HTTP {response.status} {response.status_text}"
        )

        body = parse_json(response, context="transaction")
        assert_matches_schema(body, TRANSACTION_SCHEMA, context="transaction")

        status = body.get("status")
        assert status not in TERMINAL_ERROR_STATUSES, (
            f"Транзакция {txn_id} завершилась ошибкой: status={status}, "
            f"errorCode={body.get('errorCode')}, error={body.get('error')}"
        )
        assert status in EXECUTED_STATUSES, (
            f"Транзакция {txn_id} не исполнена: status={status}, ожидалось одно из {EXECUTED_STATUSES}"
        )

    def test_executed_amount_is_one_rub(
        self, api_context: APIRequestContext, settings: Settings, created_payment: dict
    ):
        """Исполненная сумма должна остаться равной 1 ₽."""
        txn_id = created_payment["transaction"]["id"]
        response = api_context.get(
            f"/payment-history/v2/transactions/{txn_id}",
            params={"type": "OUT"},
        )
        body = parse_json(response, context="transaction")
        assert float(body["sum"]["amount"]) == 1.0, (
            f"Исполненная сумма ({body['sum']['amount']}) не равна 1 ₽"
        )
