from django.forms.widgets import TextInput

from stats.settings import env


class PlayButtonWidget(TextInput):
    template_name = 'calls/audio_button.html'

    def __init__(self, attrs=None):
        default_attrs = {'class': 'custom-play-button'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs)
        if value:
            value = f'{env("FTP")}{value}'
            final_attrs['value'] = value
        return super().render(name, value, final_attrs, renderer)
