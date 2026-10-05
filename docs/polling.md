# Long Polling

Long Polling — режим, в котором приложение само вызывает `GET /updates` и
ждёт новые события MAX. `Dispatcher.start_polling()` ведёт marker, передаёт
updates в handlers и повторяет запрос.

MAX ограничивает Long Polling по скорости и сроку хранения событий. Активная
Webhook-подписка отключает Long Polling. Поэтому этот режим предназначен для
разработки и тестирования; production-интеграции должны использовать Webhook.

## Запуск

```python
import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.types import Message

router = Router()


@router.message()
async def echo(message: Message) -> None:
    if message.text:
        await message.answer(message.text)


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(
        bot,
        polling_timeout=30,
        allowed_updates=["message_created"],
    )


if __name__ == "__main__":
    asyncio.run(main())
```

## Параметры

`polling_timeout` передаётся в `GET /updates` как максимальное время ожидания
ответа. Transport добавляет запас к HTTP timeout, чтобы соединение не
завершилось раньше long-poll запроса.

`allowed_updates` ограничивает список типов событий. Если параметр не указан,
Dispatcher автоматически собирает типы, для которых зарегистрированы handlers.

`handle_as_tasks=True` обрабатывает updates конкурентно. При `False` следующий
update начнёт обрабатываться только после завершения текущего.

## Остановка

`Ctrl+C` отменяет основной task. Из handler или другого task можно вызвать:

```python
await dp.stop_polling()
```

По умолчанию `start_polling()` ждёт активные handler tasks и закрывает `Bot`.
Если жизненным циклом transport управляет приложение, передайте
`close_bot_session=False` и вызовите `await bot.close()` самостоятельно.

