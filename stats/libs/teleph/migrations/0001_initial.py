# Generated by Django 4.1.4 on 2024-03-25 13:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TelephCall',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(verbose_name='Дата и время')),
                ('num_from', models.CharField(max_length=255, verbose_name='Исходящий')),
                ('mark', models.CharField(max_length=255, null=True, verbose_name='Марка')),
                ('model', models.CharField(max_length=255, null=True, verbose_name='Модель')),
                ('target', models.CharField(max_length=255, null=True, verbose_name='Входящий')),
                ('moderation', models.CharField(max_length=255, null=True, verbose_name='Модерация')),
                ('call_price', models.FloatField(null=True, verbose_name='Стоимость')),
                ('price_autoru', models.FloatField(null=True, verbose_name='Стоимость авто.ру')),
                ('price_drom', models.FloatField(null=True, verbose_name='Стоимость drom')),
                ('call_status', models.CharField(max_length=1000, null=True, verbose_name='Статус звонка')),
                ('price_of_car', models.IntegerField(null=True, verbose_name='Цена автомобиля')),
                ('color', models.CharField(max_length=500, null=True, verbose_name='Цвет')),
                ('body', models.CharField(max_length=500, null=True, verbose_name='Кузов')),
                ('drive_unit', models.CharField(max_length=500, null=True, verbose_name='Привод')),
                ('engine', models.CharField(max_length=500, null=True, verbose_name='Двигатель')),
                ('equipment', models.CharField(max_length=500, null=True, verbose_name='Комплектация')),
                ('comment', models.CharField(max_length=1000, null=True, verbose_name='Остальные комментарии')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, to_field='teleph_id', verbose_name='id клиента')),
            ],
            options={
                'verbose_name': 'Телефония звонки',
                'verbose_name_plural': 'Телефония звонки',
                'db_table': 'teleph_teleph_call',
                'ordering': ['datetime'],
            },
        ),
    ]
