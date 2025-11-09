FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    WORKSPACE=/workspace

WORKDIR ${APP_HOME}

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests

RUN pip install --no-cache-dir .

VOLUME ["${WORKSPACE}"]

ENTRYPOINT ["siren"]
CMD ["scan", "/workspace"]

