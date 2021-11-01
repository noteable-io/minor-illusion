### Builder image for pip installs / venv   
ARG VERSION=3.9.7

FROM python:${VERSION}-buster as builder

RUN python3 -m venv /opt/venv

COPY ./src/requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/python -m pip install \
    -r /tmp/requirements.txt \
    --no-cache-dir \
    --disable-pip-version-check

### Base image that copies source code
FROM python:${VERSION}-slim-buster as base
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /usr/src    

COPY ./src/app ./app

### Development image
FROM base as debug
ENV PYTHONASYNCIODEBUG=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
RUN /opt/venv/bin/python -m pip install debugpy
# Optional: add --wait-for-client in CMD below to pause startup until debugger is attached
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0"]

### Testing image
FROM base as tox
RUN /opt/venv/bin/python -m pip install pytest pytest-asyncio requests
COPY ./src/tests ./tests
CMD ["python", "-m", "pytest"]


### Production image
FROM base as prod
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]