# Generated by Django 4.1.4 on 2024-08-09 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0025_alter_clientprimatel_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='call',
            name='duration',
            field=models.IntegerField(blank=True, null=True, verbose_name='Длительность'),
        ),
        migrations.AlterField(
            model_name='call',
            name='num_to',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Входящий'),
        ),
    ]
