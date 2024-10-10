from django import forms


class TransportForm(forms.Form):
    numbers = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Введите номера в столбик',
                'rows': 4,
                'class': 'form-control',  # Добавляем Bootstrap-класс
            }
        ),
        label='Номера машин',
    )
