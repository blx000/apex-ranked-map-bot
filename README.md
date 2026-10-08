# Apex Ranked Map Telegram Bot

Telegram-бот сообщает о смене карты в рейтинговом режиме Apex Legends. В сообщениях показываются английское и официальное русское название текущей карты, оставшееся время и следующая карта.

## Возможности

- автоматическая проверка ranked-ротации раз в минуту;
- уведомление каждому подписчику один раз на каждую новую ротацию;
- команды `/start`, `/map`, `/stop` и `/help`;
- кнопка «Обновить» под сообщением;
- сохранение подписок в SQLite между перезапусками;
- повтор запросов при временных ошибках API и Telegram;
- готовый Docker-образ для Railway или VPS.

Данные предоставляет неофициальный [Apex Legends Status API](https://apexlegendsapi.com/documentation).

## Что потребуется

1. Создайте бота через [@BotFather](https://t.me/BotFather) командой `/newbot` и сохраните токен.
2. Зарегистрируйте бесплатный API-ключ в [Apex Legends API Portal](https://apexlegendsapi.com/).
3. Установите Python 3.12, если хотите запускать проект локально.

## Локальный запуск

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env`, затем экспортируйте переменные и запустите бота:

```bash
set -a
source .env
set +a
python -m apex_bot
```

Файл `.env` исключён из Git. Не публикуйте токены и не добавляйте их в Docker-образ.

## Развёртывание в Railway

1. Загрузите проект в GitHub и создайте в [Railway](https://railway.com/) новый сервис из репозитория. Railway автоматически обнаружит `Dockerfile`.
2. В разделе Variables добавьте `TELEGRAM_BOT_TOKEN` и `APEX_API_KEY`. Рекомендуется пометить их как sealed variables.
3. Добавьте Volume и подключите его к пути `/app/data`.
4. Убедитесь, что у сервиса запущена ровно одна реплика. Несколько реплик нельзя использовать одновременно с Telegram long polling и общей SQLite-базой.
5. После развёртывания откройте логи: должна появиться запись `Telegram bot started`.
6. Напишите боту `/start` и проверьте `/map`.

Необязательные переменные:

| Переменная | Значение по умолчанию | Назначение |
|---|---:|---|
| `DATABASE_PATH` | `/app/data/bot.db` | Путь к SQLite |
| `POLL_INTERVAL_SECONDS` | `60` | Интервал проверки, минимум 10 секунд |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

## Docker

```bash
docker build -t apex-ranked-bot .
docker run --rm \
  -e TELEGRAM_BOT_TOKEN='...' \
  -e APEX_API_KEY='...' \
  -v apex-bot-data:/app/data \
  apex-ranked-bot
```

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
```

Тесты не используют реальные токены и не отправляют сообщения в Telegram.

