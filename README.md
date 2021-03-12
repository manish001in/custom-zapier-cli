
To use this application, please follow these steps:
1. Ensure you have PostgreSql installed.
2. Fill in the values in settings.py
3. Run the command 'python run_once.py'
4. Run celery workers and celery beat by running these commands in separate terminals:
    i. "celery worker -A zapier --loglevel=debug --concurrency=3"   
   ii. "celery -A zapier beat"
5. Activate the virtual environment by running 'source venv/bin/activate' and then run the command 'python run_here.py'.





I would recommend trying out two particular Zap possibilities.

1. Sending email data to google sheets as a row.
2. Downloading data frop dropbox if it has been changed in last certain time duration.
