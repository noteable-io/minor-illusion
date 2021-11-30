ARG PYTHON_VERSION=3.9.7

FROM python:${PYTHON_VERSION}-buster

# wait-for script to pause until cockroach db is responding per netcat
RUN wget https://raw.githubusercontent.com/eficode/wait-for/v2.1.3/wait-for \
    -O /usr/bin/wait-for && \
    chmod +x /usr/bin/wait-for 

RUN apt-get update && apt-get install tini netcat -y

# Set up poetry and install dependencies from pyproject.toml
RUN pip install poetry tox

WORKDIR /usr/src
COPY ./src .
RUN poetry install

ENV PYTHONASYNCIODEBUG=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["tini", "--"]
CMD ["/usr/src/cast.sh"]