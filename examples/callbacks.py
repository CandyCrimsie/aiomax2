from aiomax2 import F, Router
from aiomax2.types import (
    CallbackButton,
    CallbackQuery,
    InlineKeyboardAttachmentRequest,
    Keyboard,
    Message,
)

router = Router(name=__name__)


@router.message(F.text == "buttons")
async def buttons(message: Message) -> None:
    keyboard = InlineKeyboardAttachmentRequest(
        payload=Keyboard(
            buttons=[
                [CallbackButton(text="Confirm", payload="confirm")],
                [CallbackButton(text="Cancel", payload="cancel")],
            ]
        )
    )
    await message.answer("Choose", attachments=[keyboard])


@router.callback_query(F.payload == "confirm")
async def confirm(callback_query: CallbackQuery) -> None:
    await callback_query.answer(notification="Confirmed", text="Done")
