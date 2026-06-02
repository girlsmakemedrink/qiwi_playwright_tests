"""Конфигурация тестового набора.

Все значения берутся из переменных окружения (или из файла ``.env``),
чтобы в репозитории не было реальных токенов и номеров кошельков.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Код валюты "российский рубль" по ISO-4217 — используется во всём API QIWI.
RUB_CURRENCY_CODE = 643
RUB_CURRENCY_CODE_STR = "643"

# Идентификатор провайдера "Перевод на QIWI Кошелёк" (P2P).
P2P_PROVIDER_ID = 99


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_token: str
    wallet: str
    recipient_wallet: str

    @property
    def auth_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }


def load_settings() -> Settings:
    return Settings(
        base_url=os.getenv("QIWI_BASE_URL", "https://edge.qiwi.com").rstrip("/"),
        api_token=os.getenv("QIWI_API_TOKEN", "test-token"),
        wallet=os.getenv("QIWI_WALLET", "79991234567"),
        recipient_wallet=os.getenv("QIWI_RECIPIENT_WALLET", "79997654321"),
    )
