#!/bin/bash

echo "=============================="
echo "=== Starting django server ==="
echo "=============================="

python manage.py migrate

python manage.py create_admin_user

gunicorn gantt.wsgi:application -b 0.0.0.0:8000 --reload