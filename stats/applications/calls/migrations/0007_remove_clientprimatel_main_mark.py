# Generated by Django 4.1.4 on 2024-05-21 11:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0006_alter_callpricesetting_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clientprimatel',
            name='main_mark',
        ),
    ]