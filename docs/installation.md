# Установка

## Требования

- Python 3.12 или новее;
- рабочий токен бота MAX;
- доступ к `https://platform-api2.max.ru`;
- доверенный CA для TLS-цепочки API, включая сертификаты Минцифры при
  необходимости.

## Установка из GitHub

Пока проект находится в alpha-стадии, его можно установить напрямую из
репозитория:

```bash
pip install "aiomax2 @ git+https://github.com/CandyCrimsie/aiomax2.git"
```

Обычная установка сразу включает `aiohttp`, Pydantic, FastAPI и Uvicorn.
Она поддерживает и Long Polling, и Webhook: режим доставки updates выбирается
в коде или deployment configuration, а не через package extra.

После публикации на PyPI будет достаточно:

```bash
pip install aiomax2
```

## Установка для разработки

```bash
git clone https://github.com/CandyCrimsie/aiomax2.git
cd aiomax2
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Затем:

```bash
python -m pip install -e ".[dev]"
```

Токен удобно передавать через переменную окружения:

```bash
export MAX_BOT_TOKEN="..."
```

```powershell
$env:MAX_BOT_TOKEN = "..."
```

Не помещайте токен в исходный код или Git. Для дополнительных сертификатов
см. [TLS и сертификаты](certificates.md).

## Пользовательская ClientSession

```python
import os

import aiohttp

from aiomax2 import Bot

token = os.environ["MAX_BOT_TOKEN"]

async with aiohttp.ClientSession(headers={"User-Agent": "my-max-bot/1.0"}) as session:
    bot = Bot(token, session=session)
    try:
        await bot.get_my_info()
    finally:
        await bot.close()
```

`Authorization` добавляется библиотекой к каждому запросу MAX API: вручную
добавлять token в headers не нужно. Остальные пользовательские headers
сохраняются. `Bot.close()` не закрывает переданную session — ею владеет
пользователь. Даже если custom session использует
`aiohttp.TCPConnector(ssl=False)`, запросы к MAX API получают проверяющий
`SSLContext` библиотеки на уровне request. Headers этой session не переносятся
на внешние upload URL.
