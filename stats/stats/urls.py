"""statsapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='accounts/login/', permanent=False)),
    path('', include('libs.services.urls')),
    path('', include('applications.auction.urls')),
    path('', include('applications.autoconverter.urls')),
    path('', include('applications.srav.urls')),
    path('', include('applications.netcost.urls')),
    path('ads/', include('applications.ads.urls', namespace='ads_app')),
    path('accounts/', include('applications.accounts.urls', namespace='accounts_app')),
    path('', include('libs.autoru.urls')),
    path("__debug__/", include("debug_toolbar.urls")),
]
