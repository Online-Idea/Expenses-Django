from django import forms


# class SortForm(forms.Form):
#     fields = forms.ChoiceField(choices=[], label='Выберите поля для сортировки',
#                                widget=forms.Select(attrs={'class': 'form-control mb-3"'}))
class SortForm(forms.Form):
    fields = forms.ChoiceField(
        choices=[
            ('', 'Выберите поле...'),
            ('mark', 'Марка'),
            ('model', 'Модель'),
            ('complectation', 'Комплектация'),
            ('price', 'Цена'),
            ('body_type', 'Кузов'),
            ('year', 'Год'),
            ('color', 'Цвет'),
            ('price_nds', 'Цена c НДС'),
            ('engine_capacity', 'Объём двигателя'),
            ('run', 'Пробег'),
            ('engine_capacity', 'Мощность'),
            ('drive', 'Привод'),
            ('datetime_created', 'Дата создания')
        ],
        label='Для сортировки',
        widget=forms.Select(attrs={'class': 'form-control mb-3'})
    )