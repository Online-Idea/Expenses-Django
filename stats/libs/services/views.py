
from django.http import JsonResponse
from .models import *
from .serializers import ClientSerializer


def get_models_for_mark(request, mark_id):
    models = Model.objects.filter(mark_id=mark_id).values('id', 'mark', 'model')
    return JsonResponse(list(models), safe=False)


# class ClientCreateAPIView(generics.CreateAPIView):
#     queryset = Client.objects.all()
#     serializer_class = ClientSerializer
#
#     def post(self, request, *args, **kwargs):
#         # меняй данные в request перед тем как отправлять их на create
#         # request.data['name'] = f"{request.data['name']} | ye"
#         # request.data = [f"{i['name']} | ye" for i in request.data]
#         return self.create(request, *args, **kwargs)
#
