from django import forms
from django.core.cache import cache

from applications.srav.models import (AutoruParsedAd, UniqueAutoruParsedAdMark, UniqueAutoruParsedAdRegion,
                                      UniqueAutoruParsedAdDealer)
from libs.services.models import Mark


class AutoruParsedAdChooseForm(forms.Form):
    daterange = forms.CharField(max_length=255, label='Период')

    # mark_values = cache.get('autoru_parsed_ad_mark_values')
    # if not mark_values:
    #     mark_values = AutoruParsedAd.objects.values('mark').distinct()
    #     cache.set('autoru_parsed_ad_mark_values', mark_values, 86400)

    mark_values = UniqueAutoruParsedAdMark.objects.all().order_by('mark').values_list('mark__id', flat=True)
    mark_checkbox = forms.ModelMultipleChoiceField(
        queryset=Mark.objects.filter(id__in=mark_values),
        widget=forms.CheckboxSelectMultiple(attrs={'checked': False}),
    )

    # region_choices = cache.get('autoru_parsed_ad_region_choices')
    # if not region_choices:
    #     region_choices = [(region, region) for region in
    #                       AutoruParsedAd.objects.order_by('region').values_list('region', flat=True).distinct()]
    #     cache.set('autoru_parsed_ad_region_choices', region_choices, 86400)
    region_objs = UniqueAutoruParsedAdRegion.objects.all().values_list('region', flat=True).order_by('region')
    region_choices = [(region, region) for region in region_objs]
    region_checkbox = forms.MultipleChoiceField(required=False, choices=region_choices,
                                                widget=forms.CheckboxSelectMultiple(attrs={'checked': False}))


class ComparisonChooseForm(AutoruParsedAdChooseForm):
    dealer = forms.ChoiceField(label='Сравнить для', choices=[('-----', '-----')])

    def __init__(self, *args, **kwargs):
        super(ComparisonChooseForm, self).__init__(*args, **kwargs)

        # Выбор дилеров перенёс сюда чтобы не подставлялись в форму на сайте, но были для валидации
        # dealer_choices = cache.get('comparison_dealer')
        # if not dealer_choices:
        #     dealer_choices = [('-----', '-----')] + [
        #         (dealer, dealer) for dealer in AutoruParsedAd.objects.all().values_list('dealer', flat=True).distinct()
        #     ]
        #     cache.set('comparison_dealer', dealer_choices, 86400)
        dealer_objs = UniqueAutoruParsedAdDealer.objects.all().values_list('dealer', flat=True).order_by('dealer')
        dealer_choices = [('-----', '-----')] + [(dealer, dealer) for dealer in dealer_objs]
        if self.is_bound:
            self.fields['dealer'].choices = dealer_choices
