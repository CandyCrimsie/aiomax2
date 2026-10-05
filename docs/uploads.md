# Загрузка файлов

Загрузка в MAX состоит из двух этапов:

1. `POST /uploads` возвращает одноразовый URL и иногда media token.
2. Файл отправляется multipart-запросом на upload host, после чего attachment
   добавляется в сообщение.

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

Upload URL одноразовый, поэтому неоднозначные сетевые ошибки автоматически не
повторяются. Получите новый URL и повторите операцию осознанно.

Transport отделяет API session от внешних upload hosts, чтобы custom headers
не утекали на другой домен. Токен MAX добавляется явно только в протокол
загрузки изображений, где это требует актуальная документация; для остальных
upload URLs `Authorization` не добавляется.

Проверка TLS остаётся включённой. Chunked/resumable upload пока не реализован и
указан в roadmap.

