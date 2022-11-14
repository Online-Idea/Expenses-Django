# Celery tasks
from celery.app import task
from celery import shared_task
import datetime

from stats.celery import app


@app.task
def test_task():
    return f'test success at {datetime.datetime.now()}'


@shared_task
def add(a, b):
    return a + b
