from django import forms
from django.core.cache import cache

from applications.srav.models import AutoruParsedAd
from libs.services.models import Mark


class AutoruParsedAdChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')

    mark_checkbox = cache.get('autoru_parsed_ad_mark_checkbox')
    if not mark_checkbox:
        mark_checkbox = forms.ModelMultipleChoiceField(
            queryset=Mark.objects.filter(id__in=AutoruParsedAd.objects.values('mark').distinct()),
            widget=forms.CheckboxSelectMultiple(attrs={'checked': False}),
        )
        cache.set('autoru_parsed_ad_srav_mark_checkbox', mark_checkbox, 86400)

    region_choices = cache.get('autoru_parsed_ad_srav_region_choices')
    if not region_choices:
        region_choices = [(region, region) for region in
                          AutoruParsedAd.objects.order_by('region').values_list('region', flat=True).distinct()]
        cache.set('autoru_parsed_ad_srav_region_choices', region_choices, 86400)
    region_checkbox = forms.MultipleChoiceField(required=False, choices=region_choices,
                                                widget=forms.CheckboxSelectMultiple(attrs={'checked': False}))


class ComparisonChooseForm(AutoruParsedAdChooseForm):
    dealer = forms.ChoiceField(label='Сравнить для', choices=[('-----', '-----')])

    def __init__(self, *args, **kwargs):
        super(ComparisonChooseForm, self).__init__(*args, **kwargs)

        # Выбор дилеров перенёс сюда чтобы не подставлялись в форму на сайте, но были для валидации
        dealer_choices = cache.get('comparison_dealer')
        if not dealer_choices:
            dealer_choices = [('-----', '-----')] + [
                (dealer, dealer) for dealer in AutoruParsedAd.objects.all().values_list('dealer', flat=True).distinct()
            ]
            cache.set('comparison_dealer', dealer_choices, 86400)
        if self.is_bound:
            self.fields['dealer'].choices = dealer_choices
