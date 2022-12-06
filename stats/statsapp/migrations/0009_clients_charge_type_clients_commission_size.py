# Generated by Django 4.1.2 on 2022-11-29 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statsapp', '0008_alter_clients_autoru_id_alter_clients_avito_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='clients',
            name='charge_type',
            field=models.CharField(choices=[('звонки', 'звонки'), ('комиссия процент', 'комиссия процент'), ('комиссия сумма', 'комиссия сумма')], default='звонки', max_length=255, verbose_name='Тип'),
        ),
        migrations.AddField(
            model_name='clients',
            name='commission_size',
            field=models.FloatField(null=True, verbose_name='Размер комиссии'),
        ),
    ]