# Migration from aiogram 3.x

The familiar pieces deliberately keep familiar names:

| aiogram | aiomax2 | Notes |
|---|---|---|
| `Bot` | `Bot` | MAX token is sent without `Bearer` |
| `Dispatcher` | `Dispatcher` | root router |
| `Router` | `Router` | nested routers and observers |
| `Command("start")` | `Command("start")` | injects `CommandObject` |
| `F.text` | `F.text` | local expression engine |
| `Message` | `Message` | real MAX fields; id is backed by `body.mid` |
| `message.answer()` | `message.answer()` | chooses MAX `chat_id` or `user_id` |
| `FSMContext` | `FSMContext` | async storage API |
| `State`, `StatesGroup` | same names | same declaration style |

MAX-specific differences remain visible:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(notification="Confirmed")


@router.bot_started()
async def started(event: BotStartedUpdate) -> None:
    # MAX supplies chat_id, user, optional payload and locale.
    ...
```

There is no `message.chat.id` compatibility shim. Use `message.chat_id`,
`message.recipient`, or the bound shortcut appropriate to the operation. There
is no Telegram keyboard class: use MAX attachment/button models.

For production, migrate aiogram polling entry points to a webhook deployment.
The MAX documentation explicitly limits `GET /updates` to development and
testing.

