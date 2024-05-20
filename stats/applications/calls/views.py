import datetime
import logging

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets, permissions

from applications.calls.calls import get_calls_data
from applications.calls.forms import CallChooseForm, CallForm
from applications.calls.models import Call
from applications.calls.serializers import CallSerializer
from libs.services.decorators import allowed_users


# Create your views here.
@allowed_users(allowed_groups=['admin'])
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
