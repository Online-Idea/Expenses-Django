import datetime
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from applications.accounts.models import Client
from applications.netcost.netcost import calculate_netcost
from libs.services.decorators import allowed_users
from libs.services.forms import ClientChooseForm
from libs.services.utils import split_daterange


@login_required(login_url='login')
@allowed_users(allowed_groups=['admin'])
def home(request):
    if request.method == 'POST':
        form = ClientChooseForm(request.POST, user=request.user)

        if not form.is_valid():
            return HttpResponse(status=400)

        daterange = split_daterange(form.cleaned_data.get('daterange'))

        # Выбранные клиенты
        clients_checked = [c for c in request.POST.getlist('client_checkbox')]

        # Таблица себестоимости
        stats, totals = calculate_netcost(daterange['from'], daterange['to'], clients_checked)

        context = {
            'form': form,
            'clients_checked': json.dumps(clients_checked),
            'datefrom': daterange['start'],
            'dateto': daterange['end'],
            'stats': stats,
            'totals': totals,
        }
        return render(request, 'netcost/netcost.html', context)

    else:
        form = ClientChooseForm(user=request.user)

    clients = Client.objects.filter(active=True)
    today = datetime.date.today()
    year = today.year
    month = today.month
    datefrom = datetime.date(year, month, 1).strftime('%d.%m.%Y')
    dayto = today.day - 1 if today.day > 1 else 1
    dateto = datetime.date(year, month, dayto).strftime('%d.%m.%Y')
    context = {
        'form': form,
        'datefrom': datefrom,
        'dateto': dateto,
        'clients': clients,
    }
    return render(request, 'netcost/netcost.html', context)
