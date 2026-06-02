"""JSON-Schema контракты ответов QIWI API.

Схемы выведены напрямую из документации
(https://developer.qiwi.com/ru/qiwi-wallet-personal/). Они описывают
ОЖИДАЕМЫЙ формат ответа. Если реальный ответ сервиса не соответствует схеме —
это сигнал, что "с сервисом что-то не так" (см. п.1 задания).
"""
from __future__ import annotations

# --- Общие переиспользуемые блоки --------------------------------------------

_MONEY = {
    "type": "object",
    "required": ["amount", "currency"],
    "properties": {
        "amount": {"type": "number"},
        # В разных ответах currency встречается как число (643) и как строка ("643").
        "currency": {"type": ["number", "string"]},
    },
}


# --- 1. История платежей ("Получить все платежи") ----------------------------
# GET /payment-history/v2/persons/{wallet}/payments
PAYMENT_HISTORY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["data"],
    "properties": {
        "data": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["txnId", "personId", "date", "status", "type", "sum"],
                "properties": {
                    "txnId": {"type": "number"},
                    "personId": {"type": "number"},
                    "date": {"type": "string"},
                    "errorCode": {"type": ["number", "null"]},
                    "error": {"type": ["string", "null"]},
                    "status": {
                        "type": "string",
                        "enum": ["WAITING", "SUCCESS", "ERROR"],
                    },
                    "type": {
                        "type": "string",
                        "enum": ["IN", "OUT", "QIWI_CARD", "ALL"],
                    },
                    "statusText": {"type": "string"},
                    "sum": _MONEY,
                    "commission": _MONEY,
                    "total": _MONEY,
                },
            },
        },
        # Поля пагинации могут отсутствовать/быть null, если история пуста.
        "nextTxnId": {"type": ["number", "null"]},
        "nextTxnDate": {"type": ["string", "null"]},
    },
}


# --- 2. Баланс кошелька ------------------------------------------------------
# GET /funding-sources/v2/persons/{wallet}/accounts
BALANCE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["accounts"],
    "properties": {
        "accounts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["alias", "hasBalance", "currency"],
                "properties": {
                    "alias": {"type": "string"},
                    "fsAlias": {"type": "string"},
                    "bankAlias": {"type": "string"},
                    "title": {"type": "string"},
                    "type": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                        },
                    },
                    "hasBalance": {"type": "boolean"},
                    # balance == null, когда hasBalance == false.
                    "balance": {
                        "oneOf": [
                            {"type": "null"},
                            _MONEY,
                        ]
                    },
                    "currency": {"type": "number"},
                },
            },
        }
    },
}


# --- 3/4. Принятый платёж (PaymentInfo) --------------------------------------
# POST /sinap/api/v2/terms/{provider}/payments
PAYMENT_INFO_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["id", "sum", "fields", "transaction"],
    "properties": {
        "id": {"type": "string"},
        "terms": {"type": "string"},
        "comment": {"type": ["string", "null"]},
        "source": {"type": "string"},
        "sum": _MONEY,
        "fields": {
            "type": "object",
            "required": ["account"],
            "properties": {"account": {"type": "string"}},
        },
        "transaction": {
            "type": "object",
            "required": ["id", "state"],
            "properties": {
                "id": {"type": "string"},
                "state": {
                    "type": "object",
                    "required": ["code"],
                    "properties": {"code": {"type": "string"}},
                },
            },
        },
    },
}


# --- 4. Статус одной транзакции ----------------------------------------------
# GET /payment-history/v2/transactions/{transactionId}
TRANSACTION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["txnId", "status", "type", "sum"],
    "properties": {
        "txnId": {"type": "number"},
        "status": {
            "type": "string",
            "enum": ["WAITING", "SUCCESS", "ERROR"],
        },
        "type": {"type": "string", "enum": ["IN", "OUT", "QIWI_CARD"]},
        "sum": _MONEY,
        "total": _MONEY,
        "commission": _MONEY,
    },
}
