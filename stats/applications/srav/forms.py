from django import forms
from django.core.cache import cache

from applications.srav.models import AutoruParsedAd
from libs.services.models import Mark


class SravChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')
    select_all_marks = forms.BooleanField(required=False,
                                          widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))
    mark_checkbox = cache.get('srav_mark_checkbox')
    if not mark_checkbox:
        mark_checkbox = forms.ModelMultipleChoiceField(
            queryset=Mark.objects.filter(id__in=AutoruParsedAd.objects.values('mark').distinct()),
            widget=forms.CheckboxSelectMultiple(attrs={'checked': True}),
        )
        cache.set('srav_mark_checkbox', mark_checkbox, 86400)

    select_all_regions = forms.BooleanField(required=False,
                                            widget=forms.CheckboxInput(attrs={'checked': True, 'class': 'selectAll'}))

    region_choices = cache.get('srav_region_choices')
    if not region_choices:
        region_choices = [(region, region) for region in
                          AutoruParsedAd.objects.order_by('region').values_list('region', flat=True).distinct()]
        cache.set('srav_region_choices', region_choices, 86400)
    region_checkbox = forms.MultipleChoiceField(required=False, choices=region_choices,
                                                widget=forms.CheckboxSelectMultiple(attrs={'checked': True}))
