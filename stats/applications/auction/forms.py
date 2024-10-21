from django import forms
from django.core.cache import cache

from applications.auction.models import AutoruAuctionHistory
from applications.mainapp.models import Mark


class AuctionChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_marks = forms.BooleanField(required=False,
                                          widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))

    mark_values = cache.get('auction_mark_values')
    if not mark_values:
        mark_values = AutoruAuctionHistory.objects.values('mark').distinct()
        cache.set('auction_mark_values', mark_values, 86400)

    mark_checkbox = forms.ModelMultipleChoiceField(
        queryset=Mark.objects.filter(id__in=[value['mark'] for value in mark_values]),
        widget=forms.CheckboxSelectMultiple(attrs={'checked': True}),
    )

    select_all_regions = forms.BooleanField(required=False,
                                            widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))

    region_choices = cache.get('auction_region_choices')
    if not region_choices:
        region_choices = [(region, region) for region in
                          AutoruAuctionHistory.objects.order_by('autoru_region').values_list('autoru_region',
                                                                                             flat=True).distinct()]
        cache.set('auction_region_choices', region_choices, 86400)
    region_checkbox = forms.MultipleChoiceField(required=False, choices=region_choices,
                                                widget=forms.CheckboxSelectMultiple(attrs={'checked': True}))

    only_first = forms.BooleanField(required=False,
                                    widget=forms.CheckboxInput(attrs={'checked': False}),
                                    label='Только первые места', label_suffix='')

    all_dealers_filled = forms.BooleanField(required=False,
                                            widget=forms.CheckboxInput(attrs={'checked': False}),
                                            label='Все дилеры заполнены', label_suffix='')
