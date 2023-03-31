from datetime import datetime, timedelta
# Celery tasks
from celery.app import task
from celery import shared_task

from stats.celery import app
from statsapp.autoru import get_autoru_clients, get_autoru_products, get_autoru_daily, get_autoru_calls
from statsapp.teleph import get_teleph_clients, get_teleph_calls
from statsapp.converter import get_converter_tasks, get_price


def last_30_days():
    minus_30 = (datetime.now() - timedelta(days=31)).replace(hour=0, minute=0)
    yesterday = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59)
    return minus_30, yesterday


@shared_task
def autoru_products(from_=None, to=None, clients=None):
    if not from_ and not to:  # Если обе даты не заполнены то берём последние 30 дней
        from_, to = last_30_days()
    elif not from_ or not to:  # Если одна дата не заполнена то выдать ошибку
        raise ValueError('Даты должны быть либо обе заполнены либо ни одной')

    if not clients:
        clients = get_autoru_clients()

    for client in clients:
        get_autoru_products(from_, to, client)


@shared_task
def autoru_daily(from_=None, to=None, clients=None):
    if not from_ and not to:  # Если обе даты не заполнены то берём последние 30 дней
        from_, to = last_30_days()
    elif not from_ or not to:  # Если одна дата не заполнена то выдать ошибку
        raise ValueError('Даты должны быть либо обе заполнены либо ни одной')

    if not clients:
        clients = get_autoru_clients()

    for client in clients:
        get_autoru_daily(from_, to, client)


@shared_task
def autoru_calls(from_=None, to=None, clients=None):
    if not from_ and not to:  # Если обе даты не заполнены то берём последние 30 дней
        from_, to = last_30_days()
    elif not from_ or not to:  # Если одна дата не заполнена то выдать ошибку
        raise ValueError('Даты должны быть либо обе заполнены либо ни одной')

    if not clients:
        clients = get_autoru_clients()

    for client in clients:
        get_autoru_calls(from_, to, client)


@shared_task
def teleph_calls(from_=None, to=None, clients=None):
    if not from_ and not to:  # Если обе даты не заполнены то берём последние 30 дней
        from_, to = last_30_days()
    elif not from_ or not to:  # Если одна дата не заполнена то выдать ошибку
        raise ValueError('Даты должны быть либо обе заполнены либо ни одной')

    if not clients:
        clients = get_teleph_clients()

    for client in clients:
        get_teleph_calls(from_, to, client)


@shared_task
def converter_price():
    tasks = get_converter_tasks()
    for task in tasks:
        get_price(task)
