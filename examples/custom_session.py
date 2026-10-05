import asyncio
import os

import aiohttp

from aiomax2 import Bot


async def main() -> None:
    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(
        timeout=timeout,
        headers={"User-Agent": "my-max-bot/1.0"},
    ) as session:
        bot = Bot(os.environ["MAX_BOT_TOKEN"], session=session)
        try:
            me = await bot.get_my_info()
            print(me)
        finally:
            # Bot не закрывает переданную пользователем session.
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
