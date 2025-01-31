# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python
FROM python:3.13-slim

# Встановимо змінну середовища
ENV APP_HOME /app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

# Встановимо залежності всередині контейнера
# COPY pyproject.toml $APP_HOME/pyproject.toml
# COPY poetry.lock $APP_HOME/poetry.lock

# RUN pip install poetry 1.8.4
# RUN poetry config virtualenvs.create false && poetry install --only main

# Скопіюємо інші файли в робочу директорію контейнера
COPY . .

RUN mkdir -p /app/storage
# Позначимо порти, де працює застосунок всередині контейнера
EXPOSE 3000 5000

# Запустимо наш застосунок всередині контейнера
CMD ["python", "main.py"]