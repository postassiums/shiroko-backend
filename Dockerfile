FROM python:3.13-alpine as base

WORKDIR /app

COPY requirements.txt .
COPY . .

RUN pip3 install -r requirements.txt

ENTRYPOINT pip3 install -r requirements.txt && python3 .
