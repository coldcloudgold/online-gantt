#! /bin/bash


python3 manage.py migrate

python3 manage.py create_admin_user

gunicorn gantt.wsgi:application -b 0.0.0.0:8000 --reload
