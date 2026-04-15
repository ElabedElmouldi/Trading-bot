FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir ccxt pandas numpy requests

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
