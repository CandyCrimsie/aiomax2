# Участие в разработке

Спасибо за интерес к `aiomax2`. Проект следует актуальной документации MAX и
не добавляет Telegram-совместимость ценой искажения MAX API.

## Локальная настройка

```bash
git clone https://github.com/CandyCrimsie/aiomax2.git
cd aiomax2
python -m venv .venv
python -m pip install -e ".[dev]"
```

## Перед pull request

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src/aiomax2
python -m pytest
python -m mkdocs build --strict
```

Для изменения endpoint, model или event приложите ссылку на официальную
документацию MAX или строку актуальной OpenAPI-схемы. Архивный `aiomax` можно
использовать только как исторический источник идей.

Новый публичный API должен иметь typing, тесты и русскоязычный пример. Не
добавляйте секреты, реальные токены и приватные webhook URLs в fixtures.

