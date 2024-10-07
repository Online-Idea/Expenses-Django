from django.contrib.auth.views import LogoutView, LoginView
from django.urls import path, reverse_lazy
from .views import ProfileView, RegisterView
from applications.accounts.apps import AccountsConfig

# Имя пространства имен для маршрутов текущего приложения
app_name = AccountsConfig.name


urlpatterns = [
    # Путь для страницы регистрации, обрабатывается представлением RegisterView
    path('register/', RegisterView.as_view(), name='register'),

    # Путь для страницы профиля пользователя, обрабатывается представлением ProfileView
    path('profile/', ProfileView.as_view(), name='profile'),

    # Путь для страницы входа в систему, использует стандартное LoginView
    # redirect_authenticated_user=True перенаправляет уже аутентифицированных пользователей
    path('login/', LoginView.as_view(redirect_authenticated_user=True), name='login'),

    # Путь для выхода из системы, использует стандартное LogoutView
    # После выхода перенаправляет пользователя на страницу входа
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('accounts_app:login')), name='logout'),
]
