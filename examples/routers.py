import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

main_router = Router(name="main")
admin_router = Router(name="admin")
user_router = Router(name="user")


class GreetingService:
    def render(self, name: str) -> str:
        return f"Привет, {name}!"


@admin_router.message(Command("admin"))
async def admin(message: Message) -> None:
    await message.answer("Admin router")


@user_router.message(Command("hello"))
async def hello(message: Message, greetings: GreetingService) -> None:
    name = message.sender.first_name if message.sender else "пользователь"
    await message.answer(greetings.render(name))


main_router.include_router(admin_router)
main_router.include_router(user_router)


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher(greetings=GreetingService())
    dispatcher.include_router(main_router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
