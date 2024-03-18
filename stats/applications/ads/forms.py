from django import forms


class SortForm(forms.Form):
    fields = forms.ChoiceField(choices=[], label='Выберите поля для сортировки',
                               widget=forms.Select(attrs={'class': 'form-select'}))
