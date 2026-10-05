import asyncio
import os
from pathlib import Path

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router(name=__name__)


@router.message(Command("image"))
async def image(message: Message, bot: Bot) -> None:
    path = Path(os.environ.get("MAX_IMAGE_PATH", "photo.png"))
    if not await asyncio.to_thread(path.exists):
        await message.answer(f"Файл не найден: {path}")
        return
    attachment = await bot.upload_image(path)
    await message.answer("Изображение", attachments=[attachment])


@router.message(Command("media"))
async def media(message: Message, bot: Bot) -> None:
    paths = {
        "video": Path(os.environ.get("MAX_VIDEO_PATH", "clip.mp4")),
        "audio": Path(os.environ.get("MAX_AUDIO_PATH", "voice.mp3")),
        "file": Path(os.environ.get("MAX_FILE_PATH", "report.pdf")),
    }
    path_items = list(paths.values())
    exists = await asyncio.gather(
        *(asyncio.to_thread(path.exists) for path in path_items)
    )
    missing = [
        str(path)
        for path, path_exists in zip(path_items, exists, strict=True)
        if not path_exists
    ]
    if missing:
        await message.answer(f"Нет файлов: {', '.join(missing)}")
        return
    video = await bot.upload_video(paths["video"])
    audio = await bot.upload_audio(paths["audio"])
    document = await bot.upload_file(paths["file"])
    await message.answer("Видео", attachments=[video])
    await message.answer("Аудио", attachments=[audio])
    await message.answer("Файл", attachments=[document])


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
