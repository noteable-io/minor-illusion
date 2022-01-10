FROM cockroachdb/cockroach:v21.2.2 AS cockroach

FROM jupyter/minimal-notebook

COPY --from=cockroach --chown=jovyan:users /cockroach/cockroach /usr/local/bin/cockroach

COPY conda_requirements.txt /tmp/conda_requirements.txt
COPY pypi_requirements.txt /tmp/pypi_requirements.txt
RUN mamba install --yes --file /tmp/conda_requirements.txt && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

RUN python -m pip install \
    -r /tmp/pypi_requirements.txt \
    --no-cache-dir \
    --disable-pip-version-check

RUN jupyter contrib nbextension install --user

COPY --chown=jovyan:users ./config/.jupyter /home/jovyan/.jupyter
