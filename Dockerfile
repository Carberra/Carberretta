FROM python:3.11-slim

WORKDIR /app

RUN apt-get update
RUN apt-get install -y sqlite3 gcc build-essential python3-dev libxslt-dev libffi-dev libssl-dev

COPY requirements.txt ./
RUN pip install -U pip
RUN pip install -Ur requirements.txt

COPY . .

CMD ["python3", "-m", "carberretta"]
