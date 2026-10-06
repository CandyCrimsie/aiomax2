# Установка

## Требования

- Python 3.12 или новее;
- рабочий токен бота MAX;
- доступ к `https://platform-api2.max.ru`;
- доверенный CA для TLS-цепочки MAX API; см.
  [TLS и сертификаты](certificates.md).

## Установка из PyPI

Рекомендуемый способ установки:

```bash
pip install aiomax2
```

Чтобы зафиксировать версию, укажите нужную опубликованную версию явно в
команде установки или файле зависимостей.

Проверить установленную версию:

```bash
python -c "import aiomax2; print(aiomax2.__version__)"
```

## Установка development-версии

Актуальную ветку `main` можно установить напрямую из GitHub:

```bash
pip install "aiomax2 @ git+https://github.com/CandyCrimsie/aiomax2.git"
```

Development-версия может содержать изменения, которых ещё нет в последнем
релизе PyPI.

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

Токен удобно передавать через переменную окружения.

Linux/macOS:

```bash
export MAX_BOT_TOKEN="..."
```

Windows PowerShell:

```powershell
$env:MAX_BOT_TOKEN = "..."
```

Не помещайте токен в исходный код или Git.

Если Python не доверяет TLS-цепочке `platform-api2.max.ru`, настройте
системное trust store или передайте отдельный CA bundle. Подробности:
[TLS и сертификаты](certificates.md).

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
добавлять token в headers не требуется.

Остальные пользовательские headers сохраняются.

`Bot.close()` не закрывает переданную `ClientSession` — жизненным циклом
такой session управляет пользователь.

Даже если custom session создана с:

```python
aiohttp.TCPConnector(ssl=False)
```

при безопасной конфигурации по умолчанию `aiomax2` применяет собственный
проверяющий `SSLContext` на уровне HTTPS-request.

Отключить проверку сертификата можно только явно:

```python
Bot(token, verify_ssl=False)
```

Этот режим предназначен только для диагностики и не рекомендуется для
production.

Headers пользовательской API session не переносятся на внешние upload URL.
