FROM python:3.9-alpine3.13
LABEL maintainer='mikerock.tech'

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /app/requirements.txt
COPY ./requirements.txt /app/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ENV PIP_DEFAULT_TIMEOUT=100

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /app/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /app/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    adduser \
    --disabled-password \
    --no-create-home \
    django-user

ENV PATH="/py/bin:$PATH"

USER django-user