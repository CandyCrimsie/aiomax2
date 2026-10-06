# TLS и сертификаты Минцифры

MAX принимает Bot API-запросы через `https://platform-api2.max.ru` и в
[официальной документации](https://dev.max.ru/docs-api) просит добавить
сертификат Минцифры в список доверенных. Официальный источник сертификатов и
актуальных инструкций —
[Госуслуги: сертификаты для доверенного TLS](https://www.gosuslugi.ru/landing/tls).

По умолчанию aiomax2 проверяет цепочку сертификата и hostname. Если среда
Python не доверяет цепочке, обычно возникает ошибка:

```text
ssl.SSLCertVerificationError:
unable to get local issuer certificate
```

## Режим 1: системное trust store

Рекомендуемый вариант — установить необходимые CA средствами операционной
системы или Python environment и использовать безопасную конфигурацию по
умолчанию:

```python
import os

from aiomax2 import Bot

bot = Bot(os.environ["MAX_BOT_TOKEN"])
```

Если `ssl.create_default_context()` уже доверяет полной цепочке MAX, других
параметров не требуется. Процедура системной установки зависит от ОС; берите
сертификаты и инструкции из [официального источника](https://www.gosuslugi.ru/landing/tls).

## Режим 2: CA только для aiomax2

Можно добавить CA только в SSL context данного `Bot`, не изменяя глобальное
системное trust store:

```python
bot = Bot(
    os.environ["MAX_BOT_TOKEN"],
    ca_file="/etc/ssl/max-ca.pem",
)
```

aiomax2 вызывает `ssl.create_default_context()`, поэтому обычные системные
trusted CA сохраняются, а затем добавляет указанный bundle через
`load_verify_locations()`. Это рекомендуемая альтернатива системной установке,
когда глобальное изменение trust store нежелательно.

Также можно передать собственный безопасный context:

```python
import ssl

context = ssl.create_default_context()
context.load_verify_locations(cafile="/etc/ssl/max-ca.pem")

bot = Bot(os.environ["MAX_BOT_TOKEN"], ssl_context=context)
```

Пользовательский context должен сохранять `check_hostname=True` и
`verify_mode=ssl.CERT_REQUIRED`. Небезопасный custom `SSLContext` отклоняется,
чтобы случайная конфигурация не отключила проверку.

## Режим 3: небезопасная диагностика

```python
bot = Bot(
    os.environ["MAX_BOT_TOKEN"],
    verify_ssl=False,
)
```

!!! danger "Отключение проверки TLS"
    `verify_ssl=False` отключает проверку цепочки TLS-сертификата и
    аутентификацию peer по hostname. Соединение может оставаться шифрованным,
    но подлинность сервера не подтверждается: MITM на сетевом пути может
    перехватывать или изменять bot token, сообщения, callback data, metadata и
    загружаемые файлы. Используйте режим только для диагностики или если вы
    полностью понимаете последствия. Для production применяйте системный
    trusted CA или `ca_file`.

При создании transport один раз выдаётся `InsecureTLSWarning`. aiomax2 не
передаёт `ssl=False` в aiohttp: создаётся явный context с
`check_hostname=False` и `verify_mode=ssl.CERT_NONE`.

Небезопасный режим относится ко **всем исходящим HTTPS-соединениям** данного
`Bot`/`AiohttpSession`: и к `platform-api2.max.ru`, и к внешним upload URL.
Чтобы конфигурация была однозначной, запрещены комбинации:

- `verify_ssl=False` вместе с `ca_file`;
- `verify_ssl=False` вместе с `ssl_context`;
- `ca_file` вместе с `ssl_context`.

## Клиентский TLS и Webhook TLS — разные вещи

`verify_ssl` и `ca_file` управляют только исходящими запросами aiomax2.

При Long Polling бот сам вызывает:

```text
bot -> HTTPS GET platform-api2.max.ru/updates
```

При Webhook входящий поток выглядит иначе:

```text
MAX -> HTTPS https://bot.example.ru/webhook
    -> reverse proxy
    -> aiomax2
```

Но тот же бот отдельно выполняет исходящие `subscribe()`, отправку сообщений,
callback answers и uploads. Именно к этим исходящим запросам применяется
настройка `verify_ssl`.

`verify_ssl=False` **не** отключает и не обходит требования MAX к публичному
Webhook endpoint. Публичный URL всё равно должен иметь корректный HTTPS-
сертификат, которому доверяет MAX; self-signed Webhook от этого параметра не
становится допустимым. Подробности — в [Webhook guide](webhook.md).
