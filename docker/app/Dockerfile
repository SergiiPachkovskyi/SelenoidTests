FROM python:3.10

RUN apt-get update && \
    apt clean && \
    rm -rf /var/cache/apt/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000