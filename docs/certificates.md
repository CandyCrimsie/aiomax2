# TLS и сертификаты Минцифры

`aiomax2` всегда проверяет сертификат и hostname. Опции `ssl=False` и
`verify_ssl=False` не используются.

Если системное trust store уже содержит нужную цепочку, достаточно обычного
создания `Bot`:

```python
bot = Bot(token)
```

## Дополнительный CA bundle

```python
bot = Bot(
    token,
    ca_file="/path/to/russian_trusted_ca.pem",
)
```

`ssl.create_default_context()` сохраняет системные доверенные CA, после чего
bundle добавляется через `load_verify_locations`.

## Собственный SSLContext

```python
import ssl

context = ssl.create_default_context()
context.load_verify_locations(cafile="/path/to/russian_trusted_ca.pem")

bot = Bot(token, ssl_context=context)
```

Передавайте либо `ca_file`, либо `ssl_context`, но не оба значения. Не
используйте непроверенные bundle из сторонних репозиториев: получите
сертификаты из доверенного источника и контролируйте их обновление.

Эта конфигурация относится к исходящим запросам приложения. Для входящего
Webhook публичный reverse proxy должен предъявлять MAX полную доверенную
TLS-цепочку; подробности в [Webhook guide](webhook.md).
