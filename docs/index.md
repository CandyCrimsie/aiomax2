# Документация aiomax2

`aiomax2` — асинхронный framework для актуального MAX Bot API с архитектурой,
знакомой разработчикам aiogram 3.x. Telegram-сущности не эмулируются: модели,
events, attachments и ограничения соответствуют MAX.

Проект находится в статусе **Alpha**. Для production фиксируйте версию,
используйте Webhook и проверяйте changelog MAX перед обновлением.

## С чего начать

1. [Установите библиотеку](installation.md).
2. Запустите пример из [быстрого старта](quickstart.md).
3. Изучите [Router и Dispatcher](router.md), [фильтры](filters.md) и
   [обработчики](handlers.md).
4. Для production настройте [Webhook](webhook.md).
5. Проверьте [rate limits](rate-limits.md) и [TLS](certificates.md).

## Основные руководства

- [Long Polling](polling.md)
- [Webhook](webhook.md)
- [Команды](commands.md)
- [Magic filter `F`](magic-filter.md)
- [Callback и клавиатуры](callbacks.md)
- [Inline-клавиатуры](keyboards.md)
- [Форматирование текста](formatting.md)
- [FSM](fsm.md)
- [Middleware](middleware.md)
- [Загрузка файлов](uploads.md)
- [Подписки](subscriptions.md)
- [Обработка ошибок](errors.md)
- [Покрытие MAX API](api-coverage.md)
- [Миграция с aiogram](migration-from-aiogram.md)

Главные источники истины проекта —
[официальная документация MAX](https://dev.max.ru/docs-api) и
[официальная OpenAPI-схема](https://github.com/max-messenger/api-schema).
