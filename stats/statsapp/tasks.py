from datetime import datetime, timedelta
import pandas as pd
# Celery tasks
from celery.app import task
from celery import shared_task
from django.db.models import Q
from openpyxl.workbook import Workbook

from stats.celery import app
from statsapp.autoru import get_autoru_clients, get_autoru_products, get_autoru_daily, get_autoru_calls, \
    get_auction_history, prepare_auction_history, auction_history_drop_unknown, add_auction_history, post_feeds_task
from statsapp.export import export_calls_to_file, export_calls_for_callback
from statsapp.email_sender import send_email_to_client
from statsapp.models import Clients, TelephCalls
from statsapp.teleph import get_teleph_clients, get_teleph_calls
from statsapp.converter import get_converter_tasks, get_price
from statsapp.utils import last_30_days


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
    else:
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        from_ = datetime.strptime(from_, date_format)
        to = datetime.strptime(to, date_format)

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
def converter_price(task_ids=None):
    tasks = get_converter_tasks(task_ids)
    for task in tasks:
        get_price(task)


@shared_task
def export_calls():
    calls_file = export_calls_to_file()
    # send_email_to_client('evgen0nlin3@gmail.com', [calls_file])


@shared_task
def export_callback():
    export_calls_for_callback()

@shared_task
def auction_history(client_ids=None):
    if client_ids:
        clients = Clients.objects.filter(Q(id__in=client_ids) & Q(autoru_id__isnull=False))
    else:
        clients = Clients.objects.filter(Q(active=True) & Q(autoru_id__isnull=False))
    # clients = Clients.objects.filter(id__in=[46, 48])
    # clients = Clients.objects.filter(id__in=[1])
    datetime_ = datetime.today()
    responses = [get_auction_history(client) for client in clients]

    dfs = [prepare_auction_history(data=response, datetime_=datetime_) for response in responses if response]
    if dfs:
        all_bids = pd.concat(dfs)
        all_bids = auction_history_drop_unknown(all_bids)

        add_auction_history(all_bids)


@shared_task
def post_autoru_xml(client_id: int, section: str, price_url: str,
                    delete_sale: bool = True, leave_services: bool = True,
                    leave_added_images: bool = False, is_active: bool = True):
    response = post_feeds_task(client_id, section, price_url, delete_sale, leave_services, leave_added_images, is_active)

