# Generated by Django 4.1.2 on 2022-11-29 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statsapp', '0007_alter_models_mark'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clients',
            name='autoru_id',
            field=models.IntegerField(blank=True, null=True, unique=True, verbose_name='id авто.ру'),
        ),
        migrations.AlterField(
            model_name='clients',
            name='avito_id',
            field=models.IntegerField(blank=True, null=True, unique=True, verbose_name='id авито'),
        ),
        migrations.AlterField(
            model_name='clients',
            name='drom_id',
            field=models.IntegerField(blank=True, null=True, unique=True, verbose_name='id drom'),
        ),
    ]