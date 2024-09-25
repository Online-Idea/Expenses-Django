# Generated by Django 4.1.4 on 2024-06-25 10:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('teleph', '0002_alter_telephcall_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telephcall',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='id клиента'),
        ),
    ]
