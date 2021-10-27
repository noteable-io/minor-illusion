FROM jupyter/minimal-notebook

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install \
    -r /tmp/requirements.txt \
    --no-cache-dir \
    --disable-pip-version-check

RUN jupyter contrib nbextension install --user

COPY --chown=jovyan:users ./config/.jupyter /home/jovyan/.jupyter
