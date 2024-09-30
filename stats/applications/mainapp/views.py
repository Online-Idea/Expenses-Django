from django.http import JsonResponse

from applications.mainapp.models import Model


def get_models_for_mark(request, mark_id):
    models = Model.objects.filter(mark_id=mark_id).values('id', 'mark', 'name')
    return JsonResponse(list(models), safe=False)

