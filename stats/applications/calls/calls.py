import json

from applications.calls.forms import CallChooseForm
from libs.services.utils import split_daterange


def get_calls_data(request, form):
    daterange_str = form.cleaned_data.get('daterange')
    daterange = split_daterange(daterange_str)

    clients_checked = [c for c in request.POST.getlist('client_checkbox')]

    filter_params = {
        'daterange': daterange_str,
        'clients_checked': clients_checked,
    }

    context = {
        'form': form,
        'clients_checked': json.dumps(clients_checked),
        'datefrom': daterange['start'],
        'dateto': daterange['end'],
        'datefrom_dt': daterange['from'],
        'dateto_dt': daterange['to'],
        'filter_params': filter_params,
    }
    return context

