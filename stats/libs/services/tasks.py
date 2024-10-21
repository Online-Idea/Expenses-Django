from celery import shared_task
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from applications.accounts.models import Client
from applications.auction.auction import get_and_add_auction_history
from applications.autoconverter.converter import get_converter_tasks, get_price, avilon_custom_task, \
    get_price_without_converter
from applications.autoconverter.models import ConverterTask
from applications.calls.calltouch import CalltouchLogic
from applications.calls.models import Call
from applications.calls.primatel import PrimatelLogic
from libs.autoru.autoru import update_autoru_catalog, update_marks_and_models, update_autoru_catalog2, post_feeds_task, \
    get_autoru_ads, take_out_ids, activate_autoru_ads, stop_autoru_ads, delete_autoru_ads
from libs.teleph.teleph import get_teleph_clients, get_teleph_calls
from .exkavator import modify_exkavator_xml
from .export import export_calls_to_file, export_calls_for_callback
from applications.accounts.models import Client
from libs.teleph.teleph import get_teleph_clients, get_teleph_calls
from .utils import last_30_days
from ..autoru.refactor_autoru import AutoruLogic, get_autoru_clients


@shared_task
def autoru_catalog():
    # update_autoru_catalog()
    update_marks_and_models()
    update_autoru_catalog2()


@shared_task
def autoru_products(from_=None, to=None, clients=None):
    if not from_ and not to:  # Если обе даты не заполнены то берём последние 30 дней
        from_, to = last_30_days()
    elif not from_ or not to:  # Если одна дата не заполнена то выдать ошибку
        raise ValueError('Даты должны быть либо обе заполнены либо ни одной')

    if not clients:
        clients = get_autoru_clients()

    logic = AutoruLogic()
    for client in clients:
        logic.get_and_add_products(from_, to, client)


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
        from_ = timezone.make_aware(from_)
        to = timezone.make_aware(to)

    if not clients:
        clients = get_autoru_clients()

    logic = AutoruLogic()
    for client in clients:
        logic.get_and_add_calls(from_, to, client)


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
    get_and_add_auction_history(clients)


@shared_task
def post_autoru_xml(task_id: int, section: str, delete_sale: bool = True, leave_services: bool = True,
                    leave_added_images: bool = False, is_active: bool = True):
    # response = post_feeds_task(client_id, section, price_url, delete_sale, leave_services, leave_added_images, is_active)
    task = ConverterTask.objects.get(id=task_id)
    autoru_id = str(task.client.autoru_id)
    price_url = task.autoru_xml
    logic = AutoruLogic()
    response = logic.post_feeds_task(autoru_id=autoru_id, section=section, price_url=price_url, delete_sale=delete_sale,
                                     leave_services=leave_services, leave_added_images=leave_added_images,
                                     is_active=is_active)
    return response


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
def get_primatel_data(from_: str = None, to: str = None, download_records: bool = True):
    if not from_ or not to:
        from_ = datetime.today() - timedelta(days=1)
        to = datetime.today()
    else:
        from_ = datetime.strptime(from_, "%d.%m.%Y")
        to = datetime.strptime(to, "%d.%m.%Y")
    logic = PrimatelLogic()
    logic.update_data(from_, to, download_records)


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
    from_ = timezone.make_aware(from_)
    to = timezone.make_aware(to)

    logic = CalltouchLogic()
    logic.get_calltouch_data(from_, to)
    calls = Call.objects.filter(datetime__gte=from_, datetime__lte=to)
    calls = logic.update_calls_with_calltouch_data(calls)
    logic.send_our_data_to_calltouch(calls)
    logic.check_tags(from_, to)


@shared_task
def avilon_custom():
    avilon_custom_task()
