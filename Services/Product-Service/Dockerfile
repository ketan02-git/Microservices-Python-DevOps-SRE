
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv

COPY app.py .
COPY templates/ templates/

EXPOSE 4001

USER 10001

CMD ["gunicorn", "--bind", "0.0.0.0:4001", "--workers", "2", "--access-logfile", "-", "app:app"]
