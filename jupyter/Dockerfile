FROM cockroachdb/cockroach:v21.2.2 AS cockroach

FROM jupyter/minimal-notebook

COPY --from=cockroach --chown=jovyan:users /cockroach/cockroach /usr/local/bin/cockroach

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install \
    -r /tmp/requirements.txt \
    --no-cache-dir \
    --disable-pip-version-check

RUN jupyter contrib nbextension install --user

COPY --chown=jovyan:users ./config/.jupyter /home/jovyan/.jupyter
