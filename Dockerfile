FROM python:3.11-slim-bullseye as base_image

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV POETRY_VIRTUALENVS_IN_PROJECT=0 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY --from=ghcr.io/ufoscout/docker-compose-wait:latest /wait /wait

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir poetry==1.5.1

RUN poetry install --no-root --without dev && \
    rm -rf $POETRY_CACHE_DIR

COPY ./ ./

RUN python manage.py collectstatic --noinput

CMD /wait && ./entrypoint.sh
