FROM gitpod/workspace-full

# Set up Python and install Backend libraries to 
# /home/gitpod/.cache/pypoetry/virtualenvs/minor-illusion-<hash>-py3.9
RUN pyenv install 3.9.7 && \
    curl -sSL https://install.python-poetry.org | python -

COPY --chown=gitpod:gitpod backend/src/pyproject.toml /tmp/pyproject.toml
COPY --chown=gitpod:gitpod backend/src/poetry.lock /tmp/poetry.lock

WORKDIR /tmp
RUN pyenv local 3.9.7 && \
    poetry install

 