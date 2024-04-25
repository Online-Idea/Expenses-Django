from .models import Registration
from django.forms import ModelForm


class ApplicationForm(ModelForm):
    class Meta:
        model = Registration
        fields = ['username', 'email', 'comment']
