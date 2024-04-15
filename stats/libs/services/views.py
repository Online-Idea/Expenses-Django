from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .forms import LoginUserForm
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


# class LoginUser(LoginView):
#     template_name = 'services/login.html'
#
#     def get_success_url(self):
#         return reverse_lazy('home')
#
#
# def logout_user(request):
#     logout(request)
#     return redirect('login')
