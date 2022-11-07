from statsapp.models import *
from django.db.models import *
from django.db import connection
import datetime
from django.utils import timezone

datefrom = datetime.datetime(2022, 10, 1, 00, 00, 00, 629013, tzinfo=datetime.timezone.utc)
dateto = datetime.datetime(2022, 10, 1, 23, 59, 59, 629013, tzinfo=datetime.timezone.utc)
# q = AutoruCalls.objects\
#     .select_related('client__name')\
#     .filter(datetime__gte=datefrom, datetime__lte=dateto)\
#     .values('client_id', 'client__name')\
#     .annotate(calls_sum=Sum('billing_cost'))
c = Clients.objects \
    .select_related('autorucalls__billing_cost', 'autoruproducts__total', 'telephcalls__call_price') \
    .values('id', 'name', 'autoru_id', 'teleph_id') \
    .filter(autorucalls__datetime__gte=datefrom, autorucalls__datetime__lte=dateto,
            autoruproducts__date__gte=datefrom, autoruproducts__date__lte=dateto,
            telephcalls__datetime__gte=datefrom, telephcalls__datetime__lte=dateto) \
    .annotate(calls_sum=Sum('autorucalls__billing_cost'), products_sum=Sum('autoruproducts__total'),
              teleph_calls_sum=Sum('telephcalls__call_price'))
d = Clients.objects \
    .values('id', 'name', 'autoru_id', 'teleph_id') \
    .filter(autorucalls__datetime__gte=datefrom, autorucalls__datetime__lte=dateto,
            autoruproducts__date__gte=datefrom, autoruproducts__date__lte=dateto) \
    .annotate(calls_sum=Sum('autorucalls__billing_cost'), products_sum=Sum('autoruproducts__total'))
d = Clients.objects \
    .values('id', 'name', 'autoru_id', 'teleph_id') \
    .filter(autorucalls__billing_cost__gt=0)
print(d.query)
b = Clients.objects.raw(f"""
SELECT id, name, autoru_id, teleph_id
FROM statsapp_clients
FULL JOIN
    (SELECT client_id, SUM(billing_cost) AS calls_sum
    FROM statsapp_autorucalls
    WHERE (datetime >= '{datefrom}' AND datetime <= '{dateto}')
    GROUP BY client_id) calls
ON (statsapp_clients.autoru_id = calls.client_id)
""")
b[0]
b = Clients.objects.raw(f"""
SELECT
	clients.name AS Клиент, 
	COALESCE(teleph_calls_sum, 0) AS "Приход с площадки",
	COALESCE(calls_sum, 0) + COALESCE(products_sum, 0) AS "Траты на площадку", 
	COALESCE(calls_sum, 0) AS "Траты на звонки", 
	COALESCE(products_sum, 0) AS "Траты на услуги",
	COALESCE(teleph_target, 0) AS "Звонки с площадки",
	round(COALESCE((COALESCE(calls_sum, 0) + COALESCE(products_sum, 0)) / teleph_target, 0)::DECIMAL, 2)::TEXT AS "Цена звонка",
	round(COALESCE(COALESCE(teleph_calls_sum, 0) / teleph_target, 0)::DECIMAL, 2)::TEXT AS "Цена клиента",
	round((COALESCE(COALESCE(teleph_calls_sum, 0) / teleph_target, 0) - COALESCE((COALESCE(calls_sum, 0) + COALESCE(products_sum, 0)) / teleph_target, 0))::DECIMAL, 2)::TEXT AS "Маржа",
	round((COALESCE(teleph_target, 0) * (COALESCE(COALESCE(teleph_calls_sum, 0) / teleph_target, 0) - COALESCE((COALESCE(calls_sum, 0) + COALESCE(products_sum, 0)) / teleph_target, 0)))::DECIMAL, 2)::TEXT AS "Заработок"        
FROM (SELECT id, name, autoru_id, teleph_id
	FROM clients) clients
	FULL JOIN
		(SELECT client_id, SUM(billing_cost) AS calls_sum
		FROM statsapp_autorucalls
		WHERE (datetime >= '{datefrom}' AND datetime <= '{dateto}')
		GROUP BY client_id) calls
	ON (clients.autoru_id = calls.client_id)
	FULL JOIN
		(SELECT client_id, SUM(total) AS products_sum
		FROM statsapp_autoruproducts
		WHERE (date >= '{datefrom}' AND date <= '{dateto}')
		GROUP BY client_id) products
	ON (clients.autoru_id = products.client_id)
	FULL JOIN
		(SELECT client_id, SUM(call_price) AS teleph_calls_sum, COUNT(target) AS teleph_target
		FROM statsapp_telephcalls
		WHERE (datetime >= '{datefrom}' AND datetime <= '{dateto}')
			AND (target = 'Да' OR target = 'ПМ - Целевой')
			AND moderation LIKE 'М%'
		GROUP BY client_id) teleph_calls
	ON (clients.teleph_id = teleph_calls.client_id)
""")

for i, v in enumerate(b):
    print(b[i].calls_sum)


# TODO make different querysets for each table, then combine them to one (or send all querysets to index.html)
from django.db.models import Q
clients = Clients.objects \
    .values('id', 'name', 'autoru_id', 'teleph_id') \
    .filter(active=True)
autorucalls = AutoruCalls.objects \
    .values('client_id') \
    .filter(datetime__gte=datefrom, datetime__lte=dateto) \
    .annotate(calls_sum=Sum('billing_cost'))
autoruproducts = AutoruProducts.objects \
    .values('client_id') \
    .filter(date__gte=datefrom, date__lte=dateto) \
    .annotate(products_sum=Sum('total'))
telephcalls = TelephCalls.objects \
    .values('client_id') \
    .filter((Q(datetime__gte=datefrom) & Q(datetime__lte=dateto))
            & (Q(target='Да') | Q(target='ПМ - Целевой'))
            & Q(moderation__startswith='М')) \
    .annotate(teleph_calls_sum=Sum('call_price'), teleph_target=Count('target'))
autorucalls_dict = {}
for row in autorucalls:
    autorucalls_dict[row['client_id']] = {'calls_sum': row['calls_sum']}
autoruproducts_dict = {}
for row in autoruproducts:
    autoruproducts_dict[row['client_id']] = {'products_sum': row['products_sum']}
telephcalls_dict = {}
for row in telephcalls:
    telephcalls_dict[row['client_id']] = {'teleph_calls_sum': row['teleph_calls_sum'],
                                          'teleph_target': row['teleph_target']}

# TODO добавить к клиенту оставшиеся столбцы таблицы и передать в index.html
for client in clients:
    try:
        calls_sum = autorucalls_dict[client['autoru_id']]['calls_sum']
    except KeyError:
        calls_sum = 0
    try:
        products_sum = autoruproducts_dict[client['autoru_id']]['products_sum']
    except KeyError:
        products_sum = 0
    try:
        teleph_calls_sum = telephcalls_dict[client['teleph_id']]['teleph_calls_sum']
        teleph_target = telephcalls_dict[client['teleph_id']]['teleph_target']
    except KeyError:
        teleph_calls_sum = 0
        teleph_target = 0

    client['calls_sum'] = calls_sum
    client['products_sum'] = products_sum
    client['teleph_calls_sum'] = teleph_calls_sum
    client['teleph_target'] = teleph_target
    client['platform'] = calls_sum + products_sum
    if teleph_target > 0:
        client['call_cost'] = client['platform'] / teleph_target
        client['client_cost'] = teleph_calls_sum / teleph_target
    else:
        client['call_cost'] = client['client_cost'] = 0
    client['margin'] = client['client_cost'] - client['call_cost']
    client['profit'] = client['margin'] * teleph_target

from itertools import chain
result = list(chain(clients, autorucalls, autoruproducts, telephcalls))
