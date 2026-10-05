import asyncio
import os

from aiomax2 import Bot


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    try:
        success = await bot.subscribe(
            os.environ["MAX_WEBHOOK_URL"],
            secret=os.environ["MAX_WEBHOOK_SECRET"],
            update_types=["message_created", "message_callback", "bot_started"],
        )
        print(f"Подписка создана: {success}")
        print(await bot.get_subscriptions())
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
