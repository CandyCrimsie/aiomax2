# TLS и сертификаты Минцифры

MAX Bot API доступен через:

```text
https://platform-api2.max.ru
```

Для проверки TLS-цепочки этого домена среда, в которой работает бот, должна
доверять сертификатам Национального удостоверяющего центра Минцифры России.

Для этого **не требуется выпускать собственный сертификат**.

Используются уже выпущенные CA-сертификаты:

- `Russian Trusted Root CA` — корневой сертификат;
- `Russian Trusted Sub CA` — выпускающий сертификат.

Официальная страница распространения сертификатов:

https://www.gosuslugi.ru/crt

Прямые ссылки на PEM-файлы:

```text
https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt
https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt
```

По умолчанию `aiomax2` использует безопасный TLS-режим:

```python
bot = Bot(token)
```

Проверяются:

- цепочка сертификата;
- доверенный удостоверяющий центр;
- hostname сервера.

Если необходимая CA-цепочка отсутствует в trust store, Python обычно вернёт
ошибку:

```text
ssl.SSLCertVerificationError:
certificate verify failed: unable to get local issuer certificate
```

Есть три варианта настройки.

---

## Способ 1: установить сертификаты в систему

Это рекомендуемый вариант для серверов и рабочих станций, на которых MAX API
используется постоянно.

После установки сертификатов в системное trust store дополнительная
конфигурация `aiomax2` не требуется:

```python
import os

from aiomax2 import Bot

bot = Bot(os.environ["MAX_BOT_TOKEN"])
```

### Debian / Ubuntu

Скачайте оба сертификата:

```bash
cd /usr/local/share/ca-certificates

sudo curl -O \
  https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt

sudo curl -O \
  https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt
```

Обновите системное хранилище:

```bash
sudo update-ca-certificates
```

После этого приложение можно запускать без `ca_file`:

```python
bot = Bot(token)
```

Проверить используемые Python пути сертификатов можно командой:

```bash
python -c "import ssl; print(ssl.get_default_verify_paths())"
```

Практическая проверка:

```python
import asyncio
import os

from aiomax2 import Bot


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])

    try:
        me = await bot.get_my_info()
        print(me)
    finally:
        await bot.close()


asyncio.run(main())
```

Если запрос выполняется без `CERTIFICATE_VERIFY_FAILED`, TLS trust настроен
корректно.

### Windows

Сертификаты можно установить через системное хранилище сертификатов Windows.

Корневой сертификат:

```text
russian_trusted_root_ca_pem.crt
```

должен быть добавлен в:

```text
Trusted Root Certification Authorities
```

Выпускающий сертификат:

```text
russian_trusted_sub_ca_pem.crt
```

должен быть добавлен в:

```text
Intermediate Certification Authorities
```

После этого обычной конфигурации достаточно:

```python
bot = Bot(token)
```

> Устанавливайте CA-сертификаты только из доверенного официального источника.
> Добавление корневого CA в системное хранилище распространяет доверие к нему
> на другие приложения системы.

---

## Способ 2: использовать отдельный CA bundle

Если изменять системное trust store нежелательно, сертификаты можно использовать
только внутри конкретного приложения `aiomax2`.

Скачайте оба PEM-файла:

```bash
curl -O \
  https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt

curl -O \
  https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt
```

Объедините их в один PEM bundle:

```bash
cat \
  russian_trusted_root_ca_pem.crt \
  russian_trusted_sub_ca_pem.crt \
  > russian_trusted_ca.pem
```

Полученный файл содержит два сертификата подряд:

```text
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----

-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
```

Это не новый сертификат и не новая цепочка, выпущенная пользователем.
`russian_trusted_ca.pem` — только удобный bundle из существующих CA.

Передайте его в `Bot`:

```python
import os

from aiomax2 import Bot

bot = Bot(
    os.environ["MAX_BOT_TOKEN"],
    ca_file="/path/to/russian_trusted_ca.pem",
)
```

`aiomax2` создаёт стандартный проверяющий `SSLContext` и дополнительно загружает
сертификаты из `ca_file`.

Системные доверенные CA при этом сохраняются.

Этот способ удобен:

- в виртуальных окружениях;
- Docker-контейнерах;
- на системах без административного доступа;
- если CA требуется только одному приложению.

Также можно самостоятельно создать безопасный `SSLContext`:

```python
import ssl

from aiomax2 import Bot

context = ssl.create_default_context()
context.load_verify_locations(
    cafile="/path/to/russian_trusted_ca.pem",
)

bot = Bot(
    token,
    ssl_context=context,
)
```

Пользовательский `SSLContext` должен сохранять:

```text
check_hostname = True
verify_mode = ssl.CERT_REQUIRED
```

Небезопасный custom `SSLContext` библиотека отклоняет.

---

## Способ 3: отключить проверку сертификата

Для диагностики можно явно отключить TLS certificate verification:

```python
import os

from aiomax2 import Bot

bot = Bot(
    os.environ["MAX_BOT_TOKEN"],
    verify_ssl=False,
)
```

!!! danger "Не используйте этот режим в production"
    `verify_ssl=False` отключает проверку цепочки сертификата и hostname.

    HTTPS-соединение при этом может оставаться зашифрованным, но приложение
    больше не подтверждает, что подключилось именно к настоящему серверу MAX.

    Злоумышленник, способный выполнить MITM-атаку на сетевом пути, потенциально
    сможет перехватывать или изменять:

    - bot token;
    - сообщения;
    - callback data;
    - metadata;
    - загружаемые файлы;
    - ответы MAX API.

При использовании этого режима `aiomax2` выдаёт:

```text
InsecureTLSWarning
```

Небезопасный режим применяется ко всем исходящим HTTPS-соединениям данного
`Bot`/`AiohttpSession`, включая:

```text
platform-api2.max.ru
```

и внешние upload URL.

`aiomax2` не использует `ssl=False` в отдельных aiohttp requests. Вместо этого
создаётся отдельный `SSLContext`:

```text
check_hostname = False
verify_mode = ssl.CERT_NONE
```

Запрещены неоднозначные комбинации:

```python
Bot(token, verify_ssl=False, ca_file="...")
Bot(token, verify_ssl=False, ssl_context=context)
Bot(token, ca_file="...", ssl_context=context)
```

Они завершаются `ValueError`.

Используйте `verify_ssl=False` только для диагностики или временного
troubleshooting.

Для нормальной эксплуатации рекомендуется способ 1 или способ 2.

---

## Что выбрать

Для обычного сервера:

```text
системный trust store
        ↓
Bot(token)
```

Для изолированного приложения или контейнера:

```text
CA bundle
        ↓
Bot(token, ca_file="...")
```

Только для диагностики:

```text
verify_ssl=False
```

---

## Исходящий TLS и Webhook TLS

Настройки `ca_file`, `ssl_context` и `verify_ssl` относятся только к
**исходящим соединениям** `aiomax2`.

При Long Polling:

```text
bot
  -> HTTPS
  -> platform-api2.max.ru/updates
```

При Webhook входящие запросы идут в противоположном направлении:

```text
MAX
  -> HTTPS
  -> https://bot.example.ru/webhook
  -> reverse proxy
  -> aiomax2
```

При этом бот всё равно выполняет исходящие запросы:

```text
subscribe
send_message
callback answers
uploads
другие методы MAX API
```

Именно для них используются TLS-настройки `Bot`.

`verify_ssl=False` не ослабляет требования к публичному Webhook endpoint.

Webhook по-прежнему должен иметь корректный публичный HTTPS-сертификат,
которому доверяет MAX. Например, сертификат, автоматически полученный Caddy
или другим reverse proxy у публичного удостоверяющего центра.

Self-signed сертификат Webhook не становится допустимым из-за
`verify_ssl=False`.
