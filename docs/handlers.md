# Handlers и события

Handler — обычная sync или async callable, зарегистрированная в observer.
Рекомендуется использовать `async def`, поскольку MAX API и storage
асинхронны.

```python
@router.message()
async def on_message(message: Message) -> None:
    await message.answer("Получено")
```

Событие можно получить по имени параметра или аннотации типа. Остальные
аргументы берутся из context:

```python
@router.message(Command("start"))
async def start(
    message: Message,
    command: CommandObject,
    bot: Bot,
    state: FSMContext,
) -> None: ...
```

## Регистрация без декоратора

```python
router.message.register(on_message, F.text == "hello")
```

## MAX events

`router.message` получает `Message`, а `router.callback_query` — удобный
`CallbackQuery`, собранный из `MessageCallbackUpdate`. Остальные observers
получают соответствующий MAX update или его `message` согласно реализации
`extract_event`.

Не используйте Telegram-поля вроде `message.chat.id`. Для MAX доступны
`message.chat_id`, `message.recipient`, `message.sender` и `message.body`.

Необработанный event возвращает управление родительскому pipeline. Исключение
`SkipHandler` позволяет пропустить текущий handler и продолжить проверку
следующего.

