FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir .

COPY . /app/

EXPOSE 8000

CMD ["python", "run.py"]
