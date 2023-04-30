#!/bin/sh

echo "Waiting for MySQL Database Service to start..."
# Script from ./wait-for is from:
#...https://github.com/vishnubob/wait-for-it/blob/master/wait-for-it.sh
./wait-for db:3308

python manage.py makemigrations
python manage.py migrate
python manage.py loaddata initial_data.json
python manage.py runserver 0.0.0.0:8000
