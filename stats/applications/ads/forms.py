from django import forms


class SortForm(forms.Form):
    """
    Форма для выбора поля сортировки объявлений.
    """

    # Поле для выбора сортируемого поля
    fields = forms.ChoiceField(
        choices=[
            ('', 'Выберите поле...'),  # Пустое значение по умолчанию
            ('mark', 'Марка'),
            ('model', 'Модель'),
            ('complectation', 'Комплектация'),
            ('price', 'Цена'),
            ('body_type', 'Кузов'),
            ('year', 'Год'),
            ('color', 'Цвет'),
            ('price_nds', 'Цена с НДС'),
            ('engine_capacity', 'Объём двигателя'),
            ('run', 'Пробег'),
            ('power', 'Мощность'),
            ('drive', 'Привод'),
            ('datetime_created', 'Дата создания'),
        ],
        label='Для сортировки',  # Метка для поля формы
        widget=forms.Select(attrs={'class': 'form-control mb-3'})  # Виджет для отображения select с классом Bootstrap
    )
