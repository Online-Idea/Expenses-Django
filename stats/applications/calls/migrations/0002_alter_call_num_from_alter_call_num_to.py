# Generated by Django 4.1.4 on 2024-04-23 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='call',
            name='num_from',
            field=models.CharField(max_length=30, verbose_name='Исходящий'),
        ),
        migrations.AlterField(
            model_name='call',
            name='num_to',
            field=models.CharField(max_length=30, verbose_name='Входящий'),
        ),
    ]
