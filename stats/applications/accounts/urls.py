from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy
from .views import ProfileView, RegisterView
from django.contrib.auth.views import LoginView
from applications.accounts.apps import AccountsConfig

app_name = AccountsConfig.name

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('accounts_app:login')), name='logout'),
]