"""Сценарий 2. Проверка запроса баланса.

GET /funding-sources/v2/persons/{wallet}/accounts

Ключевое условие задания: баланс всегда должен быть положительным (> 0).
Проверяем рублёвый счёт кошелька (alias = "qw_wallet_rub").
"""
from __future__ import annotations

import pytest
from playwright.sync_api import APIRequestContext

from config import RUB_CURRENCY_CODE, Settings
from helpers import assert_matches_schema, parse_json
from schemas import BALANCE_SCHEMA

RUB_WALLET_ALIAS = "qw_wallet_rub"


@pytest.mark.balance
class TestBalance:
    def _get_accounts(self, api_context: APIRequestContext, settings: Settings):
        return api_context.get(f"/funding-sources/v2/persons/{settings.wallet}/accounts")

    def _accounts_body(self, api_context: APIRequestContext, settings: Settings) -> dict:
        return parse_json(
            self._get_accounts(api_context, settings), context="funding-sources/accounts"
        )

    def _rub_account(self, body: dict) -> dict:
        accounts = body.get("accounts", [])
        rub = [a for a in accounts if a.get("alias") == RUB_WALLET_ALIAS]
        assert rub, f"В ответе нет рублёвого счёта '{RUB_WALLET_ALIAS}'"
        return rub[0]

    def test_balance_endpoint_responds_with_200(self, api_context: APIRequestContext, settings: Settings):
        response = self._get_accounts(api_context, settings)
        assert response.status == 200, (
            f"Запрос баланса вернул ошибку: HTTP {response.status} {response.status_text}"
        )

    @pytest.mark.contract
    def test_balance_response_matches_contract(self, api_context: APIRequestContext, settings: Settings):
        body = self._accounts_body(api_context, settings)
        assert_matches_schema(body, BALANCE_SCHEMA, context="funding-sources/accounts")

    def test_rub_account_has_balance(self, api_context: APIRequestContext, settings: Settings):
        body = self._accounts_body(api_context, settings)
        account = self._rub_account(body)
        assert account["hasBalance"] is True, "У рублёвого счёта должен быть реальный баланс"
        assert account.get("balance"), "Объект 'balance' рублёвого счёта пуст"

    def test_balance_is_strictly_positive(self, api_context: APIRequestContext, settings: Settings):
        """Ключевая проверка: баланс всегда строго положительный (> 0)."""
        body = self._accounts_body(api_context, settings)
        account = self._rub_account(body)
        amount = account["balance"]["amount"]
        assert isinstance(amount, (int, float)), f"Баланс должен быть числом, получено: {amount!r}"
        assert amount > 0, f"Баланс должен быть положительным (> 0), фактически: {amount}"

    def test_balance_currency_is_rub(self, api_context: APIRequestContext, settings: Settings):
        body = self._accounts_body(api_context, settings)
        account = self._rub_account(body)
        assert account["balance"]["currency"] == RUB_CURRENCY_CODE, (
            f"Ожидалась валюта RUB ({RUB_CURRENCY_CODE}), получено: {account['balance']['currency']}"
        )
