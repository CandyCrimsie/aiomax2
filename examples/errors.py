import asyncio
import os

from aiomax2 import Bot
from aiomax2.exceptions import NetworkError, NotFoundError, RateLimitError


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    try:
        await bot.get_message(os.environ.get("MAX_MESSAGE_ID", "mid.unknown"))
    except NotFoundError:
        print("Сообщение не найдено")
    except RateLimitError as exc:
        print(f"Исчерпаны retries, retry_after={exc.retry_after}")
    except NetworkError as exc:
        print(f"Сетевая ошибка: {exc}")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
