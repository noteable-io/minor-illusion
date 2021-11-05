#!/bin/bash

set -e

export PYTHONPATH=.

# 1. Block until we can talk to Cockroach
python wait_for_db.py

# 2. Run alembic to ensure db is up to date
alembic upgrade head

if [ "$1" == "debug" ]; then
    export PYTHONASYNCIODEBUG=1
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1

    # Optional: add --wait-for-client in to pause startup until debugger is attached
    exec python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload --host 0.0.0.0
else
    exec uvicorn app.main:app --host 0.0.0.0
fi
