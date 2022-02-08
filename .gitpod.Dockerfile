FROM gitpod/workspace-full

# Set up Python and Poetry.  Actual library installs will happen in gitpod task inits
RUN pyenv install 3.9.7 && \
    pyenv local 3.9.7 && \
    python -m pip install poetry


 