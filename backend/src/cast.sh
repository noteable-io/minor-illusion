set -e

wait-for cockroach:26257 -- echo "Cockroach is up"

poetry run alembic upgrade head 

poetry run python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload --host 0.0.0.0
