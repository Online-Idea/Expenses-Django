from datetime import datetime, timedelta
# Celery tasks
from celery.app import task
from celery import shared_task

from stats.celery import app
from statsapp.autoru import get_autoru_clients, get_autoru_products, get_autoru_daily, get_autoru_calls
from statsapp.teleph import get_teleph_clients, get_teleph_calls


def last_30_days():
    minus_30 = (datetime.now() - timedelta(days=31)).replace(hour=0, minute=0)
    yesterday = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59)
    return minus_30, yesterday


@shared_task
def autoru_products():
    active_autoru_clients_ids = get_autoru_clients()
    from_, to = last_30_days()
    for i in range(len(active_autoru_clients_ids)):
        get_autoru_products(from_, to, active_autoru_clients_ids[i])


@shared_task
def autoru_daily():
    active_autoru_clients_ids = get_autoru_clients()
    from_, to = last_30_days()
    for i in range(len(active_autoru_clients_ids)):
        get_autoru_daily(from_, to, active_autoru_clients_ids[i])


@shared_task
def autoru_calls():
    active_autoru_clients_ids = get_autoru_clients()
    from_, to = last_30_days()
    for i in range(len(active_autoru_clients_ids)):
        get_autoru_calls(from_, to, active_autoru_clients_ids[i])


@shared_task
def teleph_calls():
    active_teleph_clients = get_teleph_clients()
    from_, to = last_30_days()
    for client in active_teleph_clients:
        get_teleph_calls(from_, to, client)
