FROM python:3-slim

RUN apt-get update && apt-get install gcc python3-dev curl -y
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN $HOME/.poetry/bin/poetry config virtualenvs.create false
RUN $HOME/.poetry/bin/poetry install --no-ansi --no-root --no-dev

COPY . .
RUN $HOME/.poetry/bin/poetry install --no-ansi --no-dev

CMD ["python3", "-m", "carberretta"]
