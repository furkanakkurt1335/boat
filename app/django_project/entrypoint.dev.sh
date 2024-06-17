#!/bin/sh

# Wait for the PostgreSQL server to start
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run database migrations and start the development server
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
