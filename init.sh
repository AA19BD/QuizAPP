#!/bin/bash

echo "Make migrations"

alembic revision --autogenerate -m "init"

echo "Run migrations"
alembic upgrade head

echo "Create initial data in DB"
python -m app.initial_data
