import datetime

from django.http import HttpResponse
from django.shortcuts import render

from applications.calls.calls import get_calls_data
from applications.calls.forms import CallChooseForm


# Create your views here.
def calls(request):
    if request.method == 'POST':
        form = CallChooseForm(request.POST)

        if not form.is_valid():
            return HttpResponse(form.errors)

        context = get_calls_data(request, form)

        return render(request, 'calls/calls.html', context)

    else:
        form = CallChooseForm()

    today = datetime.date.today()
    year = today.year
    month = today.month
    day = today.day
    datefrom = datetime.date(year, month, 1).strftime('%d.%m.%Y')
    dateto = datetime.date(year, month, day).strftime('%d.%m.%Y')

    context = {
        'form': form,
        'datefrom': datefrom,
        'dateto': dateto,
    }
    return render(request, 'calls/calls.html', context)
