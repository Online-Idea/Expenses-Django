# Generated by Django 4.1.4 on 2024-04-23 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0002_ad_salon'),
    ]

    operations = [
        migrations.AddField(
            model_name='salon',
            name='working_hours',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Время работы'),
        ),
    ]
