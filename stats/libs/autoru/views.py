from django.shortcuts import render, redirect

from .autoru import *


def autoru_catalog(request):
    update_autoru_catalog()
    return redirect('home')


def autoru_regions(request):
    update_autoru_regions()
    return redirect('home')


