import asyncio
import logging
import os
from typing import Any

from aiomax2 import BaseMiddleware, Bot, Dispatcher, Router
from aiomax2.dispatcher import NextMiddleware
from aiomax2.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = Router(name=__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: NextMiddleware,
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        logger.info("Получено событие %s", type(event).__name__)
        data["request_id"] = "example-request-id"
        return await handler(event, data)


router.message.outer_middleware(LoggingMiddleware())


@router.message()
async def handler(message: Message, request_id: str) -> None:
    await message.answer(f"request_id={request_id}")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
