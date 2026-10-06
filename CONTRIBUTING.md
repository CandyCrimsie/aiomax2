# Участие в разработке

Спасибо за интерес к aiomax2.

`aiomax2` следует актуальной документации и OpenAPI-схеме MAX.
Архитектура и developer experience могут использовать знакомые подходы из
aiogram 3.x, но модели, методы, события и ограничения MAX всегда остаются
источником истины.

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

Для изменения endpoint, модели или события приложите ссылку на официальную
документацию MAX или строку актуальной OpenAPI-схемы.

Исторические реализации и сторонние библиотеки можно использовать только как
источник идей, но не как источник истины для поведения MAX API.

Новый публичный API должен иметь typing, тесты и русскоязычный пример или
документацию.

Не добавляйте секреты, реальные токены и приватные webhook URLs в fixtures,
examples или документацию.