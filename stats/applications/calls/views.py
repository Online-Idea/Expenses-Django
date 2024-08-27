from datetime import datetime, date

import urllib.parse

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions

from applications.accounts.models import Client
from applications.calls.calls import get_calls_data, dates_for_daterange, prepare_pivot_data, make_agency_autoru_links, \
    get_last_updated_call_datetime, get_calls_pivot_data, prepare_calls_pivot_data_for_download
from applications.calls.forms import CallForm
from applications.calls.models import Call
from applications.calls.serializers import CallSerializer
from libs.services.decorators import allowed_users
from libs.services.forms import ClientChooseForm
from libs.services.utils import get_all_fields_verbose_names, make_xlsx_for_download


# @allowed_users(allowed_groups=['admin', 'client'])
# def calls(request):
#     if request.method == 'POST':
#         context = get_calls_data(request)
#         agency_autoru_links = make_agency_autoru_links(context['clients_qs'], context['datefrom_dt'],
#                                                        context['dateto_dt'])
#         call_data = (
#             Call.objects.select_related('mark', 'model', 'client_primatel__client')
#             .filter(**context['call_filters'])
#             .order_by('client_primatel__client__name', 'datetime')
#         )
#         context['agency_autoru_links'] = agency_autoru_links
#         context['call_data'] = call_data
#         return render(request, 'calls/calls.html', context)
#
#     form = ClientChooseForm()
#     datefrom, dateto = dates_for_daterange(end_of_month=True)
#     last_updated = get_last_updated_call_datetime()
#
#     context = {
#         'form': form,
#         'datefrom': datefrom,
#         'dateto': dateto,
#         'last_updated': last_updated,
#     }
#     return render(request, 'calls/calls.html', context)


@allowed_users(allowed_groups=['admin', 'listener', 'client'])
def calls(request):
    if request.method == 'POST':
        context = get_calls_data(request)
        agency_autoru_links = make_agency_autoru_links(context['clients_qs'], context['datefrom_dt'],
                                                       context['dateto_dt'])
        call_data = (
            Call.objects.select_related('mark', 'model', 'client_primatel__client')
            .filter(**context['call_filters'])
            .order_by('client_primatel__client__name', 'datetime')
        )
        context['agency_autoru_links'] = agency_autoru_links
        context['call_data'] = call_data
        return render(request, 'calls/calls.html', context)

    else:
        context = {'form': ClientChooseForm(user=request.user)}

        query_params = request.GET.copy()
        if ('datefrom' in query_params and 'dateto' in query_params
                and any(key in query_params for key in ['clients', 'num_from', 'num_to', 'client_primatels'])):
            # GET с url параметрами, показывает таблицу как при POST
            datefrom, dateto = query_params['datefrom'], query_params['dateto']
            datefrom_dt = datetime.strptime(datefrom, '%d-%m-%Y').replace(hour=0, minute=0, second=0)
            dateto_dt = datetime.strptime(dateto, '%d-%m-%Y').replace(hour=23, minute=59, second=59)
            daterange = f'{datefrom} - {dateto}'

            call_filters = {'datetime__range': [datefrom_dt, dateto_dt]}
            filter_params = {'daterange': daterange}

            if 'clients' in query_params:
                query_params['clients'] = query_params['clients'].split(',')
                client_ids = [int(client_id) for client_id in query_params['clients']]
                clients_qs = Client.objects.filter(pk__in=client_ids)
                agency_autoru_links = make_agency_autoru_links(clients_qs, datefrom_dt, dateto_dt)
                context['agency_autoru_links'] = agency_autoru_links
                call_filters['client_primatel__client__in'] = clients_qs
                context['clients_checked'] = query_params['clients']
                filter_params['clients_checked'] = context['clients_checked']

            if 'num_from' in query_params:
                call_filters['num_from'] = query_params['num_from']
                filter_params['num_from'] = query_params['num_from']

            if 'num_to' in query_params:
                call_filters['num_to'] = query_params['num_to']
                filter_params['num_to'] = query_params['num_to']

            if 'client_primatels' in query_params:
                query_params['client_primatels'] = query_params['client_primatels'].split(',')
                client_primatels = [int(client_id) for client_id in query_params['client_primatels']]
                call_filters['client_primatel__in'] = client_primatels

            call_data = (Call.objects.select_related('mark', 'model', 'client_primatel__client')
                         .filter(**call_filters)
                         .order_by('client_primatel__client__name', 'datetime')
                         )
            context['call_data'] = call_data
            context['filter_params'] = filter_params

        else:
            # Просто GET с формой
            datefrom, dateto = dates_for_daterange(end_of_month=True)

        context['datefrom'] = datefrom
        context['dateto'] = dateto
        context['last_updated'] = get_last_updated_call_datetime()
        return render(request, 'calls/calls.html', context)


@allowed_users(allowed_groups=['admin', 'listener', 'client'])
def download_calls(request):
    context = get_calls_data(request)
    columns = ['client_primatel__client__name', 'datetime', 'num_from', 'num_to', 'duration', 'mark__mark',
               'model__model', 'target', 'moderation', 'call_price', 'status', 'other_comments', 'client_name',
               'manager_name', 'car_price', 'color', 'body', 'drive', 'engine', 'complectation', 'attention', 'city',
               'num_redirect']
    call_data = (
        Call.objects.select_related('mark', 'model', 'client_primatel__client')
        .filter(**context['call_filters'])
        .order_by('client_primatel__client__name', 'datetime')
    )
    qs = call_data.values_list(*columns)
    headers = get_all_fields_verbose_names(Call)
    headers = [headers[column] for column in columns]
    wb = make_xlsx_for_download(qs, headers)

    datefrom = date(*context['datefrom'][::-1]).strftime("%d.%m.%Y")
    dateto = date(*context['dateto'][::-1]).strftime("%d.%m.%Y")
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
def new_call(request):
    form = CallForm()
    return render(request, 'calls/call_modal.html', {'call_modal_form': form, 'new_call': True})


# @allowed_users(allowed_groups=['admin', 'listener', 'client'])
# def get_calls_data(request):
#     record_id = request.GET.get('record_id')
#     record = get_object_or_404(Call, pk=record_id)
#     data = {
#         'num_from': record.num_from,
#         'num_to': record.num_to,
#         'num_redirect': record.num_redirect,
#     }
#     return JsonResponse(data)


@allowed_users(allowed_groups=['admin', 'listener'])
def edit_call(request, pk):
    # Тут только GET, POST и PUT через DRF
    record = Call.objects.get(pk=pk)
    form = CallForm(instance=record)
    context = {
        'call_modal_form': form,
        'pk': pk,
    }
    return render(request, 'calls/call_modal.html', context)


@allowed_users(allowed_groups=['admin'])
def delete_call(request, pk):
    record = Call.objects.get(pk=pk)
    record.deleted = True
    record.save()
    return JsonResponse({'message': 'Звонок успешно удалён'})


@allowed_users(allowed_groups=['admin', 'listener', 'client'])
def calls_pivot(request):
    if request.method == 'POST':
        context = get_calls_data(request)

        queryset = (Call.objects.filter(**context['call_filters'])
                    .values('datetime', 'target', 'client_primatel__client__id', 'client_primatel__client__name',
                            'call_price')
                    .order_by('client_primatel__client__name', 'datetime')
                    )
        if queryset:
            calls_pivot_data = get_calls_pivot_data(queryset, context['datefrom_dt'], context['dateto_dt'])
            context = context | calls_pivot_data  # Объединяю словари
        return render(request, 'calls/calls_pivot.html', context)

    form = ClientChooseForm(user=request.user)
    datefrom, dateto = dates_for_daterange(end_of_month=True)
    last_updated = get_last_updated_call_datetime()

    context = {
        'form': form,
        'datefrom': datefrom,
        'dateto': dateto,
        'last_updated': last_updated,
    }
    return render(request, 'calls/calls_pivot.html', context)


@allowed_users(allowed_groups=['admin', 'listener', 'client'])
def download_calls_pivot(request):
    context = get_calls_data(request)

    queryset = (Call.objects.filter(**context['call_filters'])
                .values('datetime', 'target', 'client_primatel__client__id', 'client_primatel__client__name',
                        'call_price')
                .order_by('client_primatel__client__name', 'datetime')
                )
    if queryset:
        calls_pivot_data = get_calls_pivot_data(queryset, context['datefrom_dt'], context['dateto_dt'])
        headers, rows = prepare_calls_pivot_data_for_download(calls_pivot_data)
        wb = make_xlsx_for_download(rows, headers)

        datefrom = context['datefrom_dt'].strftime("%d.%m.%Y")
        dateto = context['dateto_dt'].strftime("%d.%m.%Y")
        filename = f'Звонки. Сводная {datefrom}-{dateto}.xlsx'
        filename = urllib.parse.quote(filename)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'

        wb.save(response)

        return response

    return HttpResponse('По выбранным параметрам нет данных, попробуйте изменить период или клиентов')


@allowed_users(allowed_groups=['admin', 'listener', 'client'])
def calls_pivot_custom(request):
    if request.method == 'POST':
        context = get_calls_data(request)
        call_data = (
            Call.objects.select_related('mark', 'model', 'client_primatel__client')
            .filter(**context['call_filters'])
            .order_by('client_primatel__client__name', 'datetime')
        )
        context['call_data'] = prepare_pivot_data(call_data)
        return render(request, 'calls/calls_pivot_custom.html', context)

    form = ClientChooseForm(user=request.user)
    datefrom, dateto = dates_for_daterange(end_of_month=True)
    last_updated = get_last_updated_call_datetime()
    context = {
        'form': form,
        'datefrom': datefrom,
        'dateto': dateto,
        'last_updated': last_updated,
    }
    return render(request, 'calls/calls_pivot_custom.html', context)
