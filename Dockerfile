FROM python:3.10-slim

RUN apt-get update && apt-get install gcc python3-dev curl -y
RUN curl -sSL  https://install.python-poetry.org | python3

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN $HOME/.local/bin/poetry config virtualenvs.create false
RUN $HOME/.local/bin/poetry install --no-ansi --no-root --no-dev

COPY . .
RUN $HOME/.local/bin/poetry install --no-ansi --no-dev

CMD ["python3", "-m", "carberretta"]
