# QIWI Wallet Personal API — автотесты на Playwright (Python)

Тестовое задание: автотесты для API QIWI Кошелька на базе документации
[developer.qiwi.com](https://developer.qiwi.com/ru/qiwi-wallet-personal/#intro).

> **Важно.** Сервис нерабочий — задача показать проектирование проверок и
> сценарии тестирования на основе документации, а не получить «зелёные» прогоны.
> Тесты написаны как полноценные контрактные проверки реального API: при работающем
> сервисе они проходят, при нерабочем — осознанно падают на сетевой ошибке/несоответствии.

## Что проверяется

| # | Сценарий | Метод API | Ключевые проверки |
|---|----------|-----------|-------------------|
| 1 | Доступность сервиса | `GET /payment-history/v2/persons/{wallet}/payments` | HTTP 200, `Content-Type: application/json`, ответ соответствует контракту (JSON-Schema), `data` — массив, соблюдается лимит `rows` |
| 2 | Запрос баланса | `GET /funding-sources/v2/persons/{wallet}/accounts` | контракт ответа, рублёвый счёт `qw_wallet_rub`, **баланс строго положительный (> 0)**, валюта = рубли (643) |
| 3 | Создание платежа на 1 ₽ | `POST /sinap/api/v2/terms/99/payments` | HTTP 200, контракт `PaymentInfo`, сумма = 1 ₽, валюта = рубли, получатель совпадает с запросом, есть `transaction.id` |
| 4 | Исполнение платежа | создание + `GET /payment-history/v2/transactions/{id}` | платёж принят (`state.code == "Accepted"`), транзакция исполнена (`status == "SUCCESS"`), сумма осталась 1 ₽ |

### Идея «проверки доступности»
Берём документированный метод «Получить все платежи» и проверяем не только код
ответа, но и **формат тела** через JSON-Schema (`schemas.py`). Если структура
ответа отличается от описанной в документации — тест падает с понятным сообщением,
что и является признаком неисправности сервиса (даже при HTTP 200).

## Структура проекта

```
qiwi-playwright-tests/
├── config.py            # настройки из переменных окружения (.env)
├── helpers.py           # сборка тел запросов + валидация по JSON-Schema
├── schemas.py           # контракты ответов, выведенные из документации
├── conftest.py          # фикстуры: api_context (APIRequestContext), created_payment
├── pytest.ini           # конфигурация pytest и маркеры
├── requirements.txt
├── .env.example
└── tests/
    ├── test_service_availability.py   # сценарий 1
    ├── test_balance.py                # сценарий 2
    ├── test_create_payment.py         # сценарий 3
    └── test_execute_payment.py        # сценарий 4
```

Тесты используют Playwright **`APIRequestContext`** — встроенный HTTP-клиент
Playwright для API-тестирования (без запуска браузера).

## Postman-коллекция

Те же 4 сценария продублированы как коллекция Postman (`postman/`):

```
postman/
├── QIWI_Wallet_Personal.postman_collection.json   # запросы + тесты (pm.test)
└── QIWI_Wallet_Personal.postman_environment.json  # переменные окружения
```

Коллекция повторяет логику автотестов: в каждом запросе во вкладке **Tests**
заданы проверки (`pm.test`), включая валидацию ответа по JSON-Schema
(`pm.response.to.have.jsonSchema`), которые соответствуют контрактам из `schemas.py`.

| Папка | Запрос | Проверки |
|-------|--------|----------|
| 1. Доступность сервиса | `GET /payment-history/v2/persons/{wallet}/payments?rows=10` | HTTP 200, `application/json`, контракт, `data` — массив, лимит `rows` |
| 2. Баланс | `GET /funding-sources/v2/persons/{wallet}/accounts` | контракт, счёт `qw_wallet_rub`, баланс > 0, валюта 643 |
| 3. Создание платежа | `POST /sinap/api/v2/terms/{provider}/payments` | HTTP 200, контракт `PaymentInfo`, сумма 1 ₽, валюта рубли, получатель совпадает, есть `transaction.id` |
| 4. Исполнение платежа | `GET /payment-history/v2/transactions/{id}?type=OUT` | контракт, статус `SUCCESS`, сумма 1 ₽ |

### Как использовать
1. В Postman: **Import** → выберите оба файла из `postman/`.
2. Выберите окружение **«QIWI Wallet Personal (env)»** и заполните `qiwi_api_token`
   (тип `secret`, в репозиторий не коммитится), при необходимости — `wallet`,
   `recipient_wallet`, `base_url`.
3. Авторизация задана на уровне коллекции: `Bearer {{qiwi_api_token}}`.
4. Запросы 3 → 4 связаны: создание платежа сохраняет `transaction_id`
   в переменную коллекции, который затем использует запрос исполнения.
   Удобно прогнать всю коллекцию через **Collection Runner** в порядке папок 1→4.

Запуск из CLI (опционально, через [newman](https://github.com/postmanlabs/newman)):

```bash
newman run postman/QIWI_Wallet_Personal.postman_collection.json \
  -e postman/QIWI_Wallet_Personal.postman_environment.json \
  --env-var "qiwi_api_token=ВАШ_ТОКЕН"
```

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install                   # драйверы Playwright (для API-тестов сам браузер не нужен)
```

## Конфигурация

```bash
cp .env.example .env
# отредактируйте .env: токен, номер кошелька, кошелёк-получатель
```

| Переменная | Назначение | По умолчанию |
|------------|------------|--------------|
| `QIWI_BASE_URL` | базовый URL API | `https://edge.qiwi.com` |
| `QIWI_API_TOKEN` | Bearer-токен API | `test-token` |
| `QIWI_WALLET` | номер кошелька без `+` | `79991234567` |
| `QIWI_RECIPIENT_WALLET` | кошелёк-получатель для P2P | `79997654321` |

Реальные секреты не коммитятся: `.env` в `.gitignore`.

## Запуск

```bash
pytest                       # все тесты
pytest -m balance            # только проверка баланса
pytest -m availability       # только доступность сервиса
pytest -m payment_create     # только создание платежа
pytest -m payment_execute    # только исполнение платежа
pytest -m contract           # только контрактные проверки формата ответа
pytest --collect-only        # увидеть список тестов без обращения к сети
```

## Заметки по проектированию

- **Контракты как JSON-Schema** (`schemas.py`) — единый источник правды о формате
  ответа; одна проверка ловит сразу все отклонения от документации.
- **Зависимость сценариев 3 и 4**: исполнение проверяется на платеже, созданном
  фикстурой `created_payment`, — повторяет реальный пользовательский путь
  «создал → исполнил».
- **Конфигурация через окружение** — нет хардкода токенов/кошельков, легко
  переключать стенды (`QIWI_BASE_URL`).
- **Маркеры pytest** — удобный запуск отдельных групп проверок.
