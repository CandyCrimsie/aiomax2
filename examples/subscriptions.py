import asyncio
import os

from aiomax2 import Bot

WEBHOOK_PATH = "/webhook"


async def main() -> None:
    webhook_url = f"{os.environ['MAX_WEBHOOK_BASE_URL'].rstrip('/')}{WEBHOOK_PATH}"
    webhook_secret = os.environ["MAX_WEBHOOK_SECRET"]
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    try:
        success = await bot.subscribe(
            webhook_url,
            secret=webhook_secret,
            update_types=["message_created", "message_callback", "bot_started"],
        )
        print(f"Подписка создана: {success}")
        print(await bot.get_subscriptions())
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
