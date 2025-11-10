FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir black


COPY . .

EXPOSE ${PORT:-8700}

ENTRYPOINT ["sh", "runner.sh"]

CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:${PORT:-8700}"]