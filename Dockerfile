FROM python:3.9-alpine3.13
LABEL maintainer='mikerock.tech'

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /app/requirements.txt
COPY ./requirements.dev.txt /app/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ENV PIP_DEFAULT_TIMEOUT=100

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev && \
    /py/bin/pip install -r /app/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /app/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
    --disabled-password \
    --no-create-home \
    django-user && \
    mkdir -p /vol/web/media /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol

ENV PATH="/py/bin:$PATH"

USER django-user