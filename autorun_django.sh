cd rasafrontend
python3 manage.py makemigrations
python3 manage.py migrate --run-syncdb
python3 manage.py runserver