# NeoMarket Moderation

Микросервис для модерации товаров.

## Описание

Модуль модерации товаров, который:
1. Получает webhook-события от B2B о создании/изменении товаров
2. Запрашивает полные данные товара из B2B (GET /api/v1/products/{id})
3. Сохраняет снимки товара (до/после)
4. Предоставляет очередь для модераторов
5. Одобряет или блокирует товары с уведомлением B2B

## API Endpoints

### Webhooks (приём событий от B2B)
- `GET /api/v1/webhooks/product-event` — webhook для уведомлений о создании/изменении товара

### Очередь
- `POST /api/v1/product-moderation/get-next` — следующая карточка из очереди

### Решения
- `POST /api/v1/products/{id}/approve` — одобрить товар
- `POST /api/v1/products/{id}/decline` — заблокировать товар (с причиной)

### Справочники
- `GET /api/v1/product-blocking-reasons` — список причин блокировки

## Интеграция с B2B

### Получение событий
B2B должен отправлять POST запрос на `/api/v1/webhooks/product-event`:
```json
{
  "product_id": 123,
  "event_type": "PRODUCT_CREATED",  // или "PRODUCT_UPDATED"
  "seller_id": 456
}
```

### Уведомление об решениях
После одобрения/блокировки модерация отправляет в B2B:
- `POST /api/v1/events/product-approved` — `{product_id: int}`
- `POST /api/v1/events/product-blocked` — `{product_id: int, reason: string}`

## Запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка PostgreSQL
# 1. Создайте базу данных:
#    createdb moderation
#    или через psql: CREATE DATABASE moderation;

# 2. Настройте подключение в .env:
#    DATABASE_URL=postgresql://user:password@host:5432/moderation

# Копирование конфигурации
cp .env.example .env

# Запуск сервера
uvicorn app.main:app --reload
```

## Структура проекта

```
app/
├── main.py              # Точка входа, создание FastAPI приложения
├── config.py            # Конфигурация из .env
├── database.py          # Асинхронное подключение к PostgreSQL (asyncpg)
├── schemas.py           # Pydantic модели для запросов/ответов
├── models/product.py    # SQLAlchemy модели (ProductSnapshot, ModerationQueueItem)
├── services/
│   ├── product_service.py    # Работа с B2B API и снимками
│   └── moderation_service.py # Логика очереди и решений
└── api/
    ├── queue.py         # Роуты очереди модерации
    ├── decisions.py     # Роуты одобрения/блокировки
    ├── reference.py     # Роуты справочников
    └── webhooks.py      # Webhook приём событий от B2B
```

## Примечания

- Используется **PostgreSQL** с асинхронным драйвером `asyncpg`
- Весь стек асинхронный: `async/await` в сервисах и API роутах
- B2B API требует авторизацию — добавить токен в конфиг и заголовки запросов
- Модерация хранит только **снимки** и **очередь**, данные товара — в B2B