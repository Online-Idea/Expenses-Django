import datetime
import urllib.parse

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets, permissions

from applications.calls.calls import get_calls_data
from applications.calls.forms import CallChooseForm, CallForm
from applications.calls.models import Call
from applications.calls.serializers import CallSerializer
from libs.services.decorators import allowed_users
from libs.services.utils import get_all_fields_verbose_names, make_xlsx_for_download


# Create your views here.
@allowed_users(allowed_groups=['admin'])
def calls(request):
    if request.method == 'POST':
        context = get_calls_data(request)
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


@allowed_users(allowed_groups=['admin'])
def download_calls(request):
    context = get_calls_data(request)
    columns = ['client_primatel__client__name', 'datetime', 'num_from', 'num_to', 'duration', 'mark__mark',
               'model__model', 'target', 'moderation', 'call_price', 'status', 'other_comments', 'client_name',
               'manager_name', 'car_price', 'color', 'body', 'drive', 'engine', 'complectation', 'attention', 'city',
               'num_redirect']
    qs = context['call_data'].values_list(*columns)
    headers = get_all_fields_verbose_names(Call)
    headers = [headers[column] for column in columns]
    wb = make_xlsx_for_download(qs, headers)

    datefrom = datetime.date(*context['datefrom'][::-1]).strftime("%d.%m.%Y")
    dateto = datetime.date(*context['dateto'][::-1]).strftime("%d.%m.%Y")
    filename = f'Звонки {datefrom}-{dateto}.xlsx'
    filename = urllib.parse.quote(filename)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'

    wb.save(response)

    return response


class CallViewSet(viewsets.ModelViewSet):
    queryset = Call.objects.all()
    serializer_class = CallSerializer
    permission_classes = [permissions.IsAuthenticated]


@allowed_users(allowed_groups=['admin'])
def edit_call(request, pk):
    record = Call.objects.get(pk=pk)
    if request.method == 'POST':
        print(request.data)
        form = CallForm(request.POST, instance=record)
        if form.is_valid():
            # TODO заполнить стоимость звонка по настройкам CallPriceSetting
            # action = form.save(commit=False)
            # calculate_call_price(action)
            # action.save()
            form.save()
        else:
            print(form.errors)
    else:
        form = CallForm(instance=record)
    context = {
        'edit_modal_form': form,
        'pk': pk,
    }
    return render(request, 'calls/edit_modal.html', context)
