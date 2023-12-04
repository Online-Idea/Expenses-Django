import datetime
import json
import pickle

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from applications.srav.forms import SravChooseForm
from applications.srav.models import AutoruParsedAd
from applications.srav.serializers import AutoruParsedAdSerializer
from libs.autoru.autoru import process_parsed_ads, fill_in_auction_with_parsed_ads
from libs.services.decorators import allowed_users
from libs.services.utils import split_daterange


class AutoruParsedAdViewSet(viewsets.ModelViewSet):
    queryset = AutoruParsedAd.objects.all()
    serializer_class = AutoruParsedAdSerializer

    def create(self, request, *args, **kwargs):
        df_received, parser_datetime, region = pickle.loads(request.body)
        df_processed = process_parsed_ads(df_received, parser_datetime, region)

        serializer = self.get_serializer(data=df_processed, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # заполняю дилеров в аукционе по данным сравнительной
        fill_in_auction_with_parsed_ads(serializer.instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@allowed_users(allowed_groups=['admin'])
def srav(request):
    if request.method == 'POST':
        form = SravChooseForm(request.POST)

        if not form.is_valid():
            return HttpResponse(status=400)

        daterange = split_daterange(form.cleaned_data.get('daterange'))

        # Выбранные марки
        marks_checked = [m for m in request.POST.getlist('mark_checkbox')]
        # Выбранные регионы
        regions_checked = [r for r in request.POST.getlist('region_checkbox')]

        filter_params = {
            'datetime__gte': daterange['from'],
            'datetime__lte': daterange['to'],
            'mark_id__in': marks_checked,
            'region__in': regions_checked
        }

        srav_data = (
            AutoruParsedAd.objects.select_related(
                'mark', 'model', 'client'
            )
            .filter(**filter_params)
            .order_by('-datetime', 'region', 'mark', 'model')
        )
        context = {
            'form': form,
            'marks_checked': json.dumps(marks_checked),
            'regions_checked': json.dumps(regions_checked),
            'datefrom': daterange['start'],
            'dateto': daterange['end'],
            'srav_data': srav_data,

        }
        return render(request, 'srav/srav.html', context)

    else:
        form = SravChooseForm()

    today = datetime.date.today()
    context = {
        'form': form,
        'datefrom': today,
        'dateto': today,
    }

    return render(request, 'srav/srav.html', context)


@allowed_users(allowed_groups=['admin'])
def download_srav(request):
    return HttpResponse('hey')


def ajax_test(request):
    return render(request, 'srav/srav.html')
