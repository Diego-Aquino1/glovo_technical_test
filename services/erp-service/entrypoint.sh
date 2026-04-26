#!/bin/sh
set -e

echo "[entrypoint] Ejecutando migraciones Alembic..."
alembic upgrade head

echo "[entrypoint] Ejecutando seed de datos..."
python -m app.seed_runner

echo "[entrypoint] Iniciando ERP Service en puerto 8001..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
