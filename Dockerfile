FROM python:3.11.4-slim as build

ENV PYTHONUNBUFFERED 1

RUN mkdir /app

WORKDIR /app

COPY --from=ghcr.io/ufoscout/docker-compose-wait:latest /wait /wait

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # build-essential \
        # gcc \
        python3-dev && \
        # libssl-dev \
        # libsasl2-dev \
    python -m pip install poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock /app/

RUN  python -m pip install --upgrade pip setuptools  &&\
    poetry install --no-dev

COPY ./ /app/

RUN python manage.py collectstatic --noinput

VOLUME /app/static

CMD /wait && ./entrypoint.sh
