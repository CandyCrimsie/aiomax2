# Загрузка файлов

Загрузка в MAX состоит из двух этапов:

1. `POST /uploads` возвращает URL для загрузки и, в зависимости от типа
   медиафайла, media token.
2. Файл загружается по полученному URL.

MAX поддерживает два способа передачи файла на втором этапе:

- multipart upload;
- resumable upload.

В настоящее время high-level helpers `aiomax2` реализуют multipart upload.

Helpers выполняют оба этапа и возвращают типизированный attachment:

```python
image = await bot.upload_image("photo.png")
video = await bot.upload_video("clip.mp4")
audio = await bot.upload_audio("voice.mp3")
document = await bot.upload_file("report.pdf")

await bot.send_message(
    "Материалы",
    chat_id=123,
    attachments=[image, video],
)
```

Для bytes и file-like object требуется `filename`:

```python
image = await bot.upload_image(
    image_bytes,
    filename="photo.png",
    content_type="image/png",
)
```

По одному upload URL можно загрузить только один файл. Если требуется загрузить
ещё один файл, необходимо повторно вызвать `POST /uploads` и получить новый URL.

Неоднозначные сетевые ошибки binary upload автоматически не повторяются:
после такого сбоя библиотека не может надёжно определить, был ли файл уже
принят upload host. Повтор операции пользователь выполняет осознанно.

## `attachment.not.ready`

После успешной загрузки MAX может ещё обрабатывать attachment. Если
`POST /messages`, `PUT /messages` или message update через `POST /answers`
вернул HTTP 400 с точным кодом `attachment.not.ready`, aiomax2 повторяет именно
операцию с уже полученным token.

Политика по умолчанию: первый запрос и не более трёх повторов с паузами
0,5 / 1 / 2 секунды. Параметры можно настроить без изменения transport retry:

```python
bot = Bot(
    token,
    attachment_retries=3,
    attachment_retry_base_delay=0.5,
)
```

Другие ответы HTTP 400 не повторяются. Неоднозначная network failure обычного
`POST /messages` также не становится основанием для повтора: это могло бы
создать дубликат. Binary POST на upload URL никогда не повторяется этим механизмом.

Каждая фактическая попытка отправки, редактирования или callback message update
заново проходит через per-target limiter. Первый запрос acquire выполняет один
раз; каждый retry получает следующий slot для того же `chat_id`/`user_id`.
Binary upload этим target limiter не ограничивается.

Transport отделяет API session от внешних upload hosts, чтобы custom headers
не утекали на другой домен. Токен MAX добавляется явно только в протокол
загрузки изображений, где это требует актуальная документация; для остальных
multipart upload URL видео, аудио и файлов `Authorization` не добавляется.
API-вызов `POST /uploads` всегда получает token обычным безопасным путём.

Проверка TLS по умолчанию остаётся включённой. Явный `verify_ssl=False`
применяется и к upload hosts; последствия описаны в
[руководстве по сертификатам](certificates.md).

Resumable upload пока не реализован; high-level helpers используют multipart
upload. Поддержка resumable upload отслеживается отдельно в roadmap.

Поведение `attachment.not.ready` соответствует
[официальному описанию `POST /uploads`](https://dev.max.ru/docs-api/methods/POST/uploads).
