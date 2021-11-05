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

COPY ./src .

### Development image
FROM base as debug
RUN /opt/venv/bin/python -m pip install debugpy
CMD ["/usr/src/cast.sh", "debug"]

### Testing image
FROM base as tox
RUN /opt/venv/bin/python -m pip install pytest pytest-asyncio pytest-mock requests
COPY ./src/tests ./tests
CMD ["python", "-m", "pytest"]


### Production image
FROM base as prod
CMD ["cast.sh"]
