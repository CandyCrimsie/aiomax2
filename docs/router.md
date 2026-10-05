# Dispatcher и Router

`Dispatcher` — корневой `Router`: он принимает updates, создаёт context и FSM,
а затем запускает маршрутизацию. Обычный `Router` группирует handlers, фильтры
и middleware одной функциональной области.

```python
from aiomax2 import Dispatcher, Router

dp = Dispatcher(database="database dependency")
main_router = Router(name="main")
admin_router = Router(name="admin")
user_router = Router(name="user")

main_router.include_router(admin_router)
main_router.include_router(user_router)
dp.include_router(main_router)
```

Один router может иметь только одного родителя. Повторное подключение и циклы
считаются ошибкой конфигурации.

## Observers

У каждого router есть observers с именами актуальных MAX events:

- `message` (`message_created`);
- `callback_query` (`message_callback`);
- `message_edited`, `message_removed`;
- `comment_created`, `comment_edited`, `comment_removed`;
- `bot_started`, `bot_stopped`;
- `bot_added`, `bot_removed`, `user_added`, `user_removed`;
- dialog, title и admin-permission events из OpenAPI;
- общий `update`.

```python
@user_router.message(...)
async def handler(...):
    ...
```

## Порядок маршрутизации

Для каждого router сначала проверяется общий observer `update`, затем observer
конкретного события, после чего обходятся дочерние routers в порядке
подключения. Внутри observer handlers проверяются в порядке регистрации.
Первый handler, чьи фильтры прошли, завершает поиск.

Размещайте более специфичные handlers раньше общих:

```python
@router.message(F.text == "help")
async def help_handler(message: Message) -> None: ...


@router.message()
async def fallback(message: Message) -> None: ...
```

## Context injection

Handler получает только запрошенные именованные зависимости. В context всегда
доступны как минимум `bot`, `dispatcher`, `router`, `update`, event и FSM
`state`. Пользовательские зависимости можно передать в `Dispatcher`:

```python
dp = Dispatcher(service=my_service)


@router.message()
async def handler(message: Message, service: Service, bot: Bot) -> None:
    await service.process(message)
```

Фильтры и middleware также могут добавлять значения в context.

