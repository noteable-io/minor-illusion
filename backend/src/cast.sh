#!/bin/bash

set -e

wait-for cockroach:26257 -- echo "Cockroach is up"

if [[ -n "$RUN_ALEMBIC" ]]; then
    poetry run alembic upgrade head 
fi

poetry run python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload --host 0.0.0.0
