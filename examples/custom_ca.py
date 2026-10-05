import asyncio
import os

from aiomax2 import Bot


async def main() -> None:
    bot = Bot(
        os.environ["MAX_BOT_TOKEN"],
        ca_file=os.environ["MAX_CA_FILE"],
    )
    try:
        print(await bot.get_my_info())
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
