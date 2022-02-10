FROM gitpod/workspace-full

# Set up Python and Poetry.  Actual library installs will happen in gitpod task inits
RUN pyenv install 3.9.7 && \
    pyenv local 3.9.7 && \
    python -m pip install poetry


# Install CockroachDB
RUN curl https://binaries.cockroachdb.com/cockroach-v21.2.5.linux-amd64.tgz | tar -xz && \
    sudo cp -i cockroach-v21.2.5.linux-amd64/cockroach /usr/local/bin/

 # Install Traefik
 RUN curl -L https://github.com/traefik/traefik/releases/download/v2.6.0/traefik_v2.6.0_linux_amd64.tar.gz | tar -zxvf - -C /tmp/
      sudo cp /tmp/traefik /usr/local/bin