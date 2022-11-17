from datetime import datetime, timedelta
# Celery tasks
from celery.app import task
from celery import shared_task

from stats.celery import app
from statsapp.autoru import get_autoru_clients, get_autoru_products, get_autoru_daily, get_autoru_calls
from statsapp.teleph import get_teleph_clients, get_teleph_calls


def last_30_days():
    minus_30 = datetime.now() - timedelta(days=31)
    yesterday = datetime.now() - timedelta(days=1)
    return minus_30, yesterday


active_autoru_clients_ids = get_autoru_clients()
active_teleph_clients = get_teleph_clients()

from_, to = last_30_days()


@shared_task
def autoru_products():
    for i in range(len(active_autoru_clients_ids)):
        get_autoru_products(from_, to, active_autoru_clients_ids[i])


@shared_task
def autoru_daily():
    for i in range(len(active_autoru_clients_ids)):
        get_autoru_daily(from_, to, active_autoru_clients_ids[i])


@shared_task
def autoru_calls():
    for i in range(len(active_autoru_clients_ids)):
        get_autoru_calls(from_, to, active_autoru_clients_ids[i])


@shared_task
def teleph_calls():
    for client in active_teleph_clients:
        get_teleph_calls(from_, to, client)
