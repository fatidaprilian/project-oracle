FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN mkdir -p /app/data /app/registry /app/reports /app/logs /app/runtime-fallback

COPY src /app/src
COPY services /app/services

WORKDIR /app

CMD ["python3", "services/api/entrypoint.py"]
