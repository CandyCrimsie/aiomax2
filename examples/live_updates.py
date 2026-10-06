from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, F, Router, TextFormat
from aiomax2.dispatcher import BaseMiddleware, NextMiddleware
from aiomax2.filters import Command, CommandObject
from aiomax2.fsm import FSMContext, State, StatesGroup
from aiomax2.types import (
    CallbackQuery,
    ContactAttachmentRequest,
    ContactAttachmentRequestPayload,
    Message,
    StickerAttachmentPayload,
    StickerAttachmentRequest,
    Update,
)
from aiomax2.utils.keyboard import InlineKeyboardBuilder

WEBHOOK_PATH = "/webhook"
MAX_WEBHOOK_BASE_URL = os.environ["MAX_WEBHOOK_BASE_URL"].rstrip("/")
MAX_WEBHOOK_SECRET = os.environ["MAX_WEBHOOK_SECRET"]
WEBHOOK_URL = f"{MAX_WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dispatcher = Dispatcher()
router = Router(name=__name__)


class LiveForm(StatesGroup):
    value = State()


def sanitize(value: Any) -> Any:
    """Redact credentials/media tokens and bound very large console values."""

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = key.casefold()
            if any(word in normalized for word in ("token", "secret", "authorization")):
                result[key] = "<redacted>"
            else:
                result[key] = sanitize(item)
        return result
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, str) and len(value) > 300:
        return f"{value[:300]}…<truncated>"
    return value


def key_ids(update: Update) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in ("chat_id", "user_id", "bot_id", "message_id", "post_id"):
        value = getattr(update, name, None)
        if value is not None:
            result[name] = value

    message = getattr(update, "message", None)
    if isinstance(message, Message):
        result.setdefault("chat_id", message.chat_id)
        result["message_id"] = message.message_id
        if message.sender is not None:
            result.setdefault("user_id", message.sender.user_id)

    callback = getattr(update, "callback", None)
    if callback is not None:
        result["callback_id"] = callback.callback_id
        result.setdefault("user_id", callback.user.user_id)
    return {key: value for key, value in result.items() if value is not None}


class UpdateConsoleLogger(BaseMiddleware):
    async def __call__(
        self,
        handler: NextMiddleware,
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        update = data["event_update"]
        print(
            json.dumps(
                {
                    "update_type": update.update_type,
                    "python_class": type(update).__name__,
                    "ids": key_ids(update),
                    "payload": sanitize(update.model_dump(mode="json")),
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        return await handler(event, data)


dispatcher.update.outer_middleware(UpdateConsoleLogger())


async def require_chat(message: Message) -> int | None:
    if message.chat_id is None:
        await message.answer("Команда требует групповой чат или канал с chat_id")
        return None
    return message.chat_id


def argument(command: CommandObject) -> str | None:
    return command.args.strip() if command.args else None


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(
        "Live harness aiomax2 0.1.0a3 запущен. "
        "Список сценариев и prerequisites: docs/live-testing.md"
    )


@router.message(Command("reply"))
async def reply(message: Message) -> None:
    await message.reply("Reply shortcut работает")


@router.message(Command("edit"))
async def edit(message: Message) -> None:
    sent = await message.answer("Сообщение до редактирования")
    await sent.edit_text("Сообщение после редактирования")


@router.message(Command("delete"))
async def delete(message: Message) -> None:
    sent = await message.answer("Это служебное сообщение будет удалено")
    await sent.delete()


@router.message(Command("buttons"))
async def buttons(message: Message) -> None:
    keyboard = (
        InlineKeyboardBuilder()
        .callback(text="Callback", payload="live-confirm")
        .link(text="MAX API", url="https://dev.max.ru/docs-api")
        .as_markup()
    )
    await message.answer("Проверьте кнопки", reply_markup=keyboard)


@router.message(Command("builder"))
async def builder(message: Message) -> None:
    keyboard = InlineKeyboardBuilder()
    keyboard.callback(text="Callback", payload="live-confirm")
    keyboard.link(text="Link", url="https://dev.max.ru/docs-api")
    keyboard.request_geo_location(text="Геопозиция", quick=False)
    keyboard.request_contact(text="Контакт")
    keyboard.message(text="/start")
    keyboard.open_app(text="Mini app", web_app="app", payload="screen-1")
    keyboard.clipboard(text="Clipboard", payload="AIOMAX2")
    keyboard.adjust(2, 2, 2, 1)
    await message.answer("Все семь MAX button types", reply_markup=keyboard.as_markup())


@router.callback_query(F.payload == "live-confirm")
async def callback(callback_query: CallbackQuery) -> None:
    result = await callback_query.answer(
        notification="Callback получен",
        text="Callback обработан",
    )
    print(f"callback answer success={result}", flush=True)


@router.message(Command("fsm"))
async def fsm(message: Message, state: FSMContext) -> None:
    await state.set_state(LiveForm.value)
    await message.answer("Отправьте произвольное значение для FSM")


@router.message(LiveForm.value)
async def fsm_value(message: Message, state: FSMContext) -> None:
    await message.answer(f"FSM получил: {message.text!r}")
    await state.clear()


@router.message(Command("me"))
async def me(message: Message, bot: Bot) -> None:
    info = await bot.get_my_info()
    await message.answer(f"bot_id={info.user_id}, name={info.full_name}")


@router.message(Command("subscriptions"))
async def subscriptions(message: Message, bot: Bot) -> None:
    items = await bot.get_subscriptions()
    lines = [f"{item.url}: {item.update_types or 'all'}" for item in items]
    await message.answer("\n".join(lines) if lines else "Подписок нет")


async def upload_from_env(
    message: Message,
    bot: Bot,
    variable: str,
    upload_method: str,
) -> None:
    configured = os.getenv(variable)
    if not configured:
        await message.answer(f"Сначала задайте {variable}")
        return
    path = Path(configured)
    attachment = await getattr(bot, upload_method)(path)
    await message.answer(f"Upload {path.name}", attachments=[attachment])


@router.message(Command("image"))
async def image(message: Message, bot: Bot) -> None:
    await upload_from_env(message, bot, "MAX_TEST_IMAGE", "upload_image")


@router.message(Command("file"))
async def file(message: Message, bot: Bot) -> None:
    await upload_from_env(message, bot, "MAX_TEST_FILE", "upload_file")


@router.message(Command("audio"))
async def audio(message: Message, bot: Bot) -> None:
    await upload_from_env(message, bot, "MAX_TEST_AUDIO", "upload_audio")


@router.message(Command("video_upload"))
async def video_upload(message: Message, bot: Bot) -> None:
    await upload_from_env(message, bot, "MAX_TEST_VIDEO", "upload_video")


@router.message(Command("ratelimit"))
async def ratelimit(message: Message) -> None:
    await asyncio.gather(
        *(message.answer(f"Rate-limit probe {index}") for index in range(1, 4))
    )


@router.message(Command("request_contact"))
async def request_contact(message: Message) -> None:
    keyboard = (
        InlineKeyboardBuilder().request_contact(text="Поделиться контактом").as_markup()
    )
    await message.answer("Отправьте контакт", reply_markup=keyboard)


@router.message(Command("clipboard"))
async def clipboard(message: Message) -> None:
    keyboard = (
        InlineKeyboardBuilder()
        .clipboard(text="Скопировать", payload="AIOMAX2")
        .as_markup()
    )
    await message.answer("Проверьте clipboard", reply_markup=keyboard)


@router.message(Command("send_contact"))
async def send_contact(message: Message, command: CommandObject) -> None:
    value = argument(command)
    if value is None or not value.isdecimal():
        await message.answer("Использование: /send_contact <numeric_user_id>")
        return
    attachment = ContactAttachmentRequest(
        payload=ContactAttachmentRequestPayload(
            name="Live test contact",
            contact_id=int(value),
        )
    )
    await message.answer("Contact attachment", attachments=[attachment])


@router.message(Command("sticker"))
async def sticker(message: Message, command: CommandObject) -> None:
    code = argument(command)
    if code is None:
        await message.answer("Использование: /sticker <sticker_code>")
        return
    attachment = StickerAttachmentRequest(payload=StickerAttachmentPayload(code=code))
    await message.answer(attachments=[attachment])


@router.message(Command("html"))
async def html(message: Message) -> None:
    await message.answer("<b>HTML</b> <i>format</i>", format=TextFormat.HTML)


@router.message(Command("markdown"))
async def markdown(message: Message) -> None:
    await message.answer("**MAX Markdown** _format_", format=TextFormat.MARKDOWN)


@router.message(Command("chat"))
async def chat(message: Message, bot: Bot) -> None:
    chat_id = await require_chat(message)
    if chat_id is None:
        return
    info = await bot.get_chat(chat_id)
    await message.answer(
        f"chat_id={info.chat_id}, type={info.type}, status={info.status}, "
        f"members={info.participants_count}"
    )


@router.message(Command("action"))
async def action(message: Message, bot: Bot) -> None:
    chat_id = await require_chat(message)
    if chat_id is not None:
        await bot.send_action(chat_id, "typing_on")
        await message.answer("typing_on отправлен")


@router.message(Command("pin"))
async def pin(message: Message, bot: Bot, command: CommandObject) -> None:
    chat_id = await require_chat(message)
    parts = argument(command).split() if argument(command) else []
    if chat_id is None:
        return
    if len(parts) != 2 or parts[1] != "CONFIRM":
        await message.answer("Использование: /pin <message_id> CONFIRM")
        return
    await bot.pin_message(chat_id, parts[0])
    await message.answer("Сообщение закреплено")


@router.message(Command("unpin"))
async def unpin(message: Message, bot: Bot, command: CommandObject) -> None:
    chat_id = await require_chat(message)
    if chat_id is None:
        return
    if argument(command) != "CONFIRM":
        await message.answer("Использование: /unpin CONFIRM")
        return
    await bot.unpin_message(chat_id)
    await message.answer("Закрепление удалено")


@router.message(Command("members"))
async def members(message: Message, bot: Bot) -> None:
    chat_id = await require_chat(message)
    if chat_id is None:
        return
    result = await bot.get_members(chat_id, count=20)
    lines = [f"{item.user_id}: {item.full_name}" for item in result.members[:20]]
    await message.answer("\n".join(lines) if lines else "Участников нет")


@router.message(Command("admins"))
async def admins(message: Message, bot: Bot) -> None:
    chat_id = await require_chat(message)
    if chat_id is None:
        return
    items = await bot.get_admins(chat_id)
    lines = [f"{item.user_id}: {item.full_name}" for item in items]
    await message.answer("\n".join(lines) if lines else "Администраторов нет")


@router.message(Command("comments"))
async def comments(message: Message, bot: Bot, command: CommandObject) -> None:
    post_id = argument(command)
    if post_id is None:
        await message.answer("Использование: /comments <post_message_id>")
        return
    items = await bot.get_comments(post_id, count=20)
    lines = [f"{item.body.mid}: {item.body.text!r}" for item in items]
    await message.answer("\n".join(lines) if lines else "Комментариев нет")


@router.message(Command("video"))
async def video(message: Message, bot: Bot, command: CommandObject) -> None:
    token = argument(command)
    if token is None:
        await message.answer("Использование: /video <video_token>")
        return
    details = await bot.get_video_attachment_details(token)
    await message.answer(
        f"video={details.width}x{details.height}, duration={details.duration}s"
    )


@router.message(Command("remove_member"))
async def remove_member(message: Message, bot: Bot, command: CommandObject) -> None:
    chat_id = await require_chat(message)
    parts = argument(command).split() if argument(command) else []
    if chat_id is None:
        return
    if len(parts) != 2 or not parts[0].isdecimal() or parts[1] != "CONFIRM":
        await message.answer(
            "Опасная операция. Использование: /remove_member <user_id> CONFIRM"
        )
        return
    await bot.remove_member(chat_id, int(parts[0]))
    await message.answer("Участник удалён")


@router.message(Command("revoke_admin"))
async def revoke_admin(message: Message, bot: Bot, command: CommandObject) -> None:
    chat_id = await require_chat(message)
    parts = argument(command).split() if argument(command) else []
    if chat_id is None:
        return
    if len(parts) != 2 or not parts[0].isdecimal() or parts[1] != "CONFIRM":
        await message.answer(
            "Опасная операция. Использование: /revoke_admin <user_id> CONFIRM"
        )
        return
    await bot.revoke_admin(chat_id, int(parts[0]))
    await message.answer("Права администратора отозваны")


@router.message(Command("leave_chat"))
async def leave_chat(message: Message, bot: Bot, command: CommandObject) -> None:
    chat_id = await require_chat(message)
    if chat_id is None:
        return
    if argument(command) != "CONFIRM":
        await message.answer("Бот покинет чат. Для подтверждения: /leave_chat CONFIRM")
        return
    await bot.leave_chat(chat_id)


async def observe_event(event: object) -> None:
    """Keep every official observer represented in the Webhook subscription."""


for observer in (
    router.message,
    router.callback_query,
    router.message_edited,
    router.message_removed,
    router.comment_created,
    router.comment_edited,
    router.comment_removed,
    router.bot_added,
    router.bot_removed,
    router.user_added,
    router.user_removed,
    router.bot_started,
    router.bot_stopped,
    router.dialog_cleared,
    router.dialog_removed,
    router.dialog_muted,
    router.dialog_unmuted,
    router.chat_title_changed,
    router.bot_admin_permissions_changed,
):
    observer.register(observe_event)


dispatcher.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await bot.subscribe(
            WEBHOOK_URL,
            secret=MAX_WEBHOOK_SECRET,
            update_types=dispatcher.resolve_used_update_types(),
        )
        yield
    finally:
        await bot.close()
        await dispatcher.close()


app = FastAPI(lifespan=lifespan)
app.include_router(
    dispatcher.webhook_router(
        WEBHOOK_PATH,
        bot=bot,
        secret=MAX_WEBHOOK_SECRET,
    )
)
