FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# system deps (curl for health/debug)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . .

CMD ["bash", "entrypoint.sh"]
