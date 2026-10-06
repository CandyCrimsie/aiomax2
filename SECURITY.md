# Политика безопасности

## Поддерживаемые версии

Пока проект находится в alpha, security fixes выпускаются только для последней
опубликованной версии и ветки `main`.

## Сообщение об уязвимости

Не публикуйте уязвимость и рабочий exploit в открытом issue. Используйте
GitHub Security Advisories репозитория (раздел **Security → Report a
vulnerability**) и укажите:

- затронутую версию;
- способ воспроизведения;
- возможное влияние;
- предлагаемый способ исправления, если он известен.

Не отправляйте реальные MAX tokens, webhook secrets, пользовательские данные
или приватные сертификаты. После подтверждения проблемы maintainer согласует
срок исправления и раскрытия.

## Базовые гарантии

`aiomax2` по умолчанию проверяет TLS certificate chain и hostname, сравнивает
Webhook secret в constant time и не отправляет token на обычные внешние upload
URLs. `verify_ssl=False` — осознанный diagnostic/compatibility escape hatch:
он отключает certificate verification и peer authentication для исходящих API
и upload HTTPS-соединений и не рекомендуется для production. HTTPS как
протокол при этом не выключается. Пользователь отвечает за хранение токена,
HTTPS reverse proxy, обновление CA bundle и общий rate limiter в multi-worker
deployment.
