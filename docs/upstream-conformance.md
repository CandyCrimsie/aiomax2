# Сверка с официальной реализацией MAX

Аудит выполнен 7 октября 2026 года по двум upstream-источникам:

- OpenAPI `0.0.33`, repository HEAD `1a4a502fab096aa3a15d83d7ea95667ffb44d2ac`
  (`schema.yaml` — `5af13bddab6a16b991cbe2640c78d02e2a3047da`);
- официальный Go SDK, ветка `v2`, commit
  `13264f872c743f55dcf7a8dfce43a16a055b46ab` (`v2.4.3`).

Wire contract определяется актуальной OpenAPI и воспроизводимым поведением
MAX. Go SDK используется как behavioral reference: для request construction,
updates, uploads, errors и retries. Он не задаёт архитектуру Python API.

## Результат по областям

| Область | Результат сверки |
|---|---|
| Bot, chats, messages, comments | Текущие endpoints, query/body shapes и response models покрыты high-level методами, кроме удалённых операций |
| Updates | Все 19 discriminator OpenAPI типизированы; 36 update/Webhook fixtures Go SDK v2 проходят parsing |
| Attachments и keyboards | Все текущие attachment и семь button types представлены; документированные сочетания вложений проверяются локально |
| Uploads | Multipart field `data`, type-specific token source и XML/empty responses согласованы с Go SDK и документацией |
| Errors и retries | Wire error сохраняется в `payload`; timeout отделён от прочих network errors; повторяется только безопасный или явно разрешённый запрос |
| Polling и Webhook | Marker, cancellation, filters, secret и HTTP response semantics сверены; механизмы доставки одновременно не запускаются |

## Осознанные различия

- В Go SDK остались legacy `GetChats`, `DeleteChat` и `AddMembers`.
  `aiomax2` их не возвращает: `GET /chats` уже удалён, а живая документация
  объявляет `POST /chats/{chatId}/members` удалённым с 30 сентября 2026 года,
  хотя OpenAPI `0.0.33` всё ещё содержит этот path.
- Go subscription body всё ещё содержит `version` и `self_signed_cert`.
  Актуальная OpenAPI их не содержит, поэтому `aiomax2` их не отправляет.
- Go upload client не добавляет Authorization на upload host. Текущий media
  guide MAX явно требует token для image upload, поэтому `aiomax2` добавляет
  его только для image flow. Video, audio и file upload не наследуют API
  Authorization.
- Go `updateRaw.FromRaw()` сводит wire events к одной плоской структуре.
  `aiomax2` сохраняет исходные typed update models. Для FSM callback actor
  берётся из `callback.user`, а не из recipient исходного сообщения: это
  пользователь, фактически нажавший кнопку.
- `bot_admin_permissions_changed` присутствует в актуальной OpenAPI и
  Webhook, но отсутствует в текущем Go `UpdateType` и пока недоступен через
  Long Polling. Событие поддерживается по контракту OpenAPI.
- Client-side rate limiting, строгий TLS, typed exception hierarchy и
  bounded `attachment.not.ready` retry — дополнительные защитные свойства
  Python-клиента, не меняющие wire contract MAX.

## Известные особенности MAX

- Comment update payload в OpenAPI называется `message` и ссылается на
  обычный `Message`, хотя comment endpoints возвращают `CommentMessage`.
  `aiomax2` следует discriminator contract без искусственной конвертации.
- Notification-only callback сериализуется по OpenAPI и в live-наблюдении
  возвращал `success=true`, `message=null`, но уведомление могло не
  отображаться в Web, Android и iOS. Библиотека не создаёт message fallback.
- Устаревшее поле `User.name` всё ещё возвращается MAX и присутствует в
  официальных Go fixtures. Оно типизировано как optional; для нового кода
  используйте `first_name` и `last_name`.
- Неизвестный будущий `update_type` остаётся generic `Update`, а новые поля
  сохраняются благодаря `extra="allow"`.

Полная таблица endpoints и эксплуатационных ограничений находится в
[покрытии API](api-coverage.md).
