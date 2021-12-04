ARG PYTHON_VERSION=3.9.7

FROM python:${PYTHON_VERSION}-buster
RUN python -m pip install mkdocs

WORKDIR /usr/src/mkdocs

COPY ./mkdocs .

CMD ["mkdocs", "serve", "--dev-addr", "0.0.0.0:8000"]