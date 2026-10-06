# Форматирование текста

MAX API принимает два значения `format`: `markdown` и `html`. Их можно
передавать строкой или через enum:

```python
from aiomax2 import TextFormat

await message.answer(
    "<b>Жирный</b> <i>курсив</i>",
    format=TextFormat.HTML,
)

await message.answer(
    "**Жирный** _курсив_",
    format=TextFormat.MARKDOWN,
)
```

Без `format` текст отправляется как plain text. `aiomax2` не парсит и не
переписывает разметку: она передаётся MAX API.

## MAX Markdown

Это диалект Markdown, описанный MAX, а не обещание полной совместимости с
CommonMark, GFM или Telegram Markdown.

| Возможность | Синтаксис |
|---|---|
| Курсив | `*текст*` или `_текст_` |
| Жирный | `**текст**` или `__текст__` |
| Зачёркнутый | `~~текст~~` |
| Подчёркнутый | `++текст++` |
| Код | `` `код` ``; блок — тройные backticks |
| Ссылка | `[MAX](https://dev.max.ru/)` |
| Упоминание MAX user | `[Имя](max://user/123456)` |
| Выделение | `^^текст^^` |
| Заголовок | `# Заголовок` |
| Цитата | `> Цитата` |

MAX API на данный момент не предоставляет отдельный version identifier для
Markdown. Используется значение `markdown` с синтаксисом из официальной
документации MAX. Поэтому `MARKDOWN_V2` в `TextFormat` не добавлен.

## HTML

Официальная документация перечисляет следующие группы тегов:

- `<i>` / `<em>` — курсив;
- `<b>` / `<strong>` — жирный;
- `<del>` / `<s>` — зачёркнутый;
- `<ins>` / `<u>` — подчёркнутый;
- `<pre>` / `<code>` — форматированный код;
- `<a href="...">` — ссылка, включая `max://user/{user_id}`;
- `<mark>` — выделение;
- `<h1>` … `<h6>` — заголовки;
- `<blockquote>` — цитата.

Собственного HTML parser в библиотеке нет. Используйте только синтаксис,
который документирует MAX.

## Поддерживаемые методы

`format` проходит без изменения через:

- `Bot.send_message()`, `Message.answer()` и `Message.reply()`;
- `Bot.edit_message()` и `Message.edit_text()`;
- `Bot.answer_callback()` / `Callback.answer()` при изменении сообщения;
- `send_comment()` и `edit_comment()`.

Для комментариев MAX отдельно указывает, что hyperlinks и user mentions не
поддерживаются. Не полагайтесь на `<a>`, Markdown links или `max://user/...` в
тексте комментария.

Актуальный синтаксис приведён в
[официальной документации MAX](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting).
