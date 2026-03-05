# MASA

**Quickstart:**

Clone this repository on github. You will be missing a .venv (Virtual environment folder), a valid .env file (Environmental variables) and db.sqlite3 file (Database file)

Use python's builtin virtual environment to create a virtual environment, then install dependencies.

Windows: 
```commandline
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt

```
macOS/Linux:
```commandline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The code on github comes with a sample.env file. Please rename it to .env and fill it in with the proper values, such as generating a new key for Django with django.core.management.utils.get_random_secret_key.


Then, set up django.

Windows:
```commandline
py manage.py makemigrations
py manage.py migrate
py manage.py runserver
```
macOS/Linux:
```commandline
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
