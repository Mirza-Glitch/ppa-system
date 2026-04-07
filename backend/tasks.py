import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', broker_url)

celery = Celery('tasks', broker=broker_url, backend=result_backend)

@celery.task
def send_daily_reminders():
    # Logic to find upcoming deadlines and send emails [cite: 120]
    print("Daily reminders sent to students.")

@celery.task
def generate_monthly_report():
    # Logic to aggregate placement stats [cite: 127]
    # Send HTML/PDF mail to Admin [cite: 128]
    print("Monthly report sent to Admin.")