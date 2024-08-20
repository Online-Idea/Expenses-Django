# Celery tasks
from celery import shared_task
from datetime import datetime

from applications.autoconverter.converter import get_converter_tasks, get_price, avilon_custom_task, \
    get_price_without_converter
from applications.calls.calltouch import CalltouchLogic
from applications.calls.models import Call
from applications.calls.primatel import PrimatelLogic
from libs.autoru.autoru import *
from .exkavator import modify_exkavator_xml
from .export import export_calls_to_file, export_calls_for_callback
from applications.accounts.models import Client
from libs.teleph.teleph import get_teleph_clients, get_teleph_calls
from .utils import last_30_days


@shared_task
def autoru_catalog():
    update_autoru_catalog()


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
        if task.use_converter:
            get_price(task)
        else:
            get_price_without_converter(task)


@shared_task
def export_calls():
    calls_file = export_calls_to_file()
    # send_email_to_client('evgen0nlin3@gmail.com', [calls_file])


@shared_task
def export_callback(from_: str = None, to: str = None):
    export_calls_for_callback(from_, to)


@shared_task
def auction_history(client_ids=None):
    if client_ids:
        clients = Client.objects.filter(Q(id__in=client_ids) & Q(autoru_id__isnull=False))
    else:
        clients = Client.objects.filter(Q(active=True) & Q(autoru_id__isnull=False))
    # clients = Client.objects.filter(id__in=[46, 48])
    # clients = Client.objects.filter(id__in=[1])
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


@shared_task
def exkavator_feed():
    modify_exkavator_xml()


@shared_task
def get_and_activate_autoru_ads(autoru_id: int):
    ads = get_autoru_ads(autoru_id)
    ads = take_out_ids(ads)
    activate_autoru_ads(ads, autoru_id)


@shared_task
def get_and_stop_autoru_ads(autoru_id: int):
    ads = get_autoru_ads(autoru_id)
    ads = take_out_ids(ads)
    stop_autoru_ads(ads, autoru_id)


@shared_task
def get_and_delete_autoru_ads(autoru_id: int):
    ads = get_autoru_ads(autoru_id)
    ads = take_out_ids(ads)
    delete_autoru_ads(ads, autoru_id)


@shared_task
def get_primatel_data(from_: str = None, to: str = None):
    # TODO если to минус from_ больше 10 то разбивать на несколько запросов по 10 дней каждый
    if not from_ or not to:
        from_ = datetime.today() - timedelta(days=1)
        to = datetime.today()
    else:
        from_ = datetime.strptime(from_, "%d.%m.%Y")
        to = datetime.strptime(to, "%d.%m.%Y")
    logic = PrimatelLogic()
    logic.update_data(from_, to)


@shared_task
def update_calltouch(from_: str = None, to: str = None):
    if not from_ or not to:
        from_ = datetime.today() - timedelta(days=1)
        to = datetime.today()
    else:
        from_ = datetime.strptime(from_, "%d.%m.%Y")
        to = datetime.strptime(to, "%d.%m.%Y")
    from_ = from_.replace(hour=0, minute=0, second=0, microsecond=0)
    to = to.replace(hour=23, minute=59, second=59, microsecond=0)

    logic = CalltouchLogic()
    logic.get_calltouch_data(from_, to)
    calls = Call.objects.filter(datetime__gte=from_, datetime__lte=to)
    calls = logic.update_calls_with_calltouch_data(calls)
    logic.send_our_data_to_calltouch(calls)
    logic.check_tags(from_, to)


@shared_task
def avilon_custom():
    avilon_custom_task()
