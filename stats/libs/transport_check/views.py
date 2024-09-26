from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from .forms import TransportForm
from .utils import solve_and_parse


class TransportCheckView(View):
    template_name = 'transport_check/index.html'

    def get(self, request):
        # Получаем результаты, если они переданы через GET параметры
        results = request.session.pop('results', None)
        form = TransportForm()
        return render(request, self.template_name, {'form': form, 'results': results})

    def post(self, request):
        form = TransportForm(request.POST)
        if form.is_valid():
            # Получаем список номеров из формы
            nomera = form.cleaned_data['numbers'].split(',')
            nomera = [n.strip() for n in nomera]

            # Парсим данные для номеров
            results = solve_and_parse(nomera)
            print(f'results: {results}')

            # Сохраняем результаты в сессии, чтобы использовать их после редиректа
            request.session['results'] = results

            # Выполняем редирект на GET-запрос (PRG)
            return HttpResponseRedirect(reverse('transport_check'))

        # Если форма невалидна, просто отобразить страницу снова
        return render(request, self.template_name, {'form': form})