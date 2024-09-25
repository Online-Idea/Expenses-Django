# Generated by Django 4.1.4 on 2024-07-30 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0011_alter_modification_battery_capacity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modification',
            name='power',
        ),
        migrations.AddField(
            model_name='modification',
            name='power_hp',
            field=models.IntegerField(default=0, verbose_name='Мощность в лошадиных силах'),
        ),
        migrations.AddField(
            model_name='modification',
            name='power_kw',
            field=models.IntegerField(default=0, verbose_name='Мощность в киловатах'),
        ),
    ]
