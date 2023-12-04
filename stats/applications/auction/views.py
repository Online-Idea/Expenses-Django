import datetime
import json
import urllib.parse

from django.http import HttpResponse
from django.shortcuts import render

from libs.services.decorators import allowed_users
from .auction import get_auction_data, plot_auction, make_xlsx_for_download
from .forms import *


# @cache_page(60)  # Кэш представления на 60 секунд
@allowed_users(allowed_groups=['admin'])
def auction(request):
    if request.method == 'POST':
        context = get_auction_data(request)

        # График plotly, только по одной марке и одному региону
        if len(json.loads(context['marks_checked'])) == 1 \
                and len(json.loads(context['regions_checked'])) == 1 \
                and context['auction_data']:
            auction_data_values = list(
                context['auction_data'].values("datetime", "autoru_region", "mark__mark", "model__model", "position",
                                               "bid", "competitors", "client__name"))
            plot_html = plot_auction(auction_data_values)
            context['plot_html'] = plot_html

        return render(request, 'auction/auction.html', context)

    else:
        form = AuctionChooseForm()

    today = datetime.date.today()
    context = {
        'form': form,
        'datefrom': today,
        'dateto': today,
    }
    return render(request, 'auction/auction.html', context)


@allowed_users(allowed_groups=['admin'])
def download_auction(request):
    context = get_auction_data(request)

    wb = make_xlsx_for_download(context)

    datefrom = datetime.date(*context['datefrom'][::-1]).strftime("%d.%m.%Y")
    dateto = datetime.date(*context['dateto'][::-1]).strftime("%d.%m.%Y")
    filename = f'Аукцион {datefrom}-{dateto}.xlsx'
    filename = urllib.parse.quote(filename)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'

    wb.save(response)

    return response
