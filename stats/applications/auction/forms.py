from django import forms
from django.core.cache import cache

from applications.auction.models import AutoruAuctionHistory
from libs.services.models import Mark


class AuctionChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_marks = forms.ChoiceField(required=False,
                                         widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    mark_checkbox = cache.get('mark_checkbox')
    if not mark_checkbox:
        mark_checkbox = forms.ModelMultipleChoiceField(
            queryset=Mark.objects.filter(id__in=AutoruAuctionHistory.objects.values('mark').distinct()),
            widget=forms.CheckboxSelectMultiple(attrs={'checked': True}),
        )
        cache.set('mark_checkbox', mark_checkbox, 86400)

    select_all_regions = forms.ChoiceField(required=False,
                                           widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))

    region_checkbox = cache.get('region_checkbox')
    if not region_checkbox:
        region_checkbox = forms.ModelMultipleChoiceField(
            queryset=AutoruAuctionHistory.objects.order_by('autoru_region').values_list('autoru_region',
                                                                                        flat=True).distinct(),
            widget=forms.CheckboxSelectMultiple(attrs={'checked': True})
        )
        cache.set('region_checkbox', region_checkbox, 86400)

    only_first = forms.ChoiceField(required=False,
                                   widget=forms.CheckboxInput(attrs={'checked': False}),
                                   label='Только первые места', label_suffix='')

    all_dealers_filled = forms.ChoiceField(required=False,
                                           widget=forms.CheckboxInput(attrs={'checked': False}),
                                           label='Все дилеры заполнены', label_suffix='')
