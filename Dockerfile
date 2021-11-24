FROM python:3-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -U pip
RUN pip install -Ur requirements.txt

COPY . .

CMD ["python3", "-m", "carberretta"]
