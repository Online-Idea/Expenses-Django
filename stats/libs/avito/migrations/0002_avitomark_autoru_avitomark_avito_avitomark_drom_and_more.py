# Generated by Django 4.1.4 on 2024-05-06 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('avito', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='avitomark',
            name='autoru',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Авто.ру'),
        ),
        migrations.AddField(
            model_name='avitomark',
            name='avito',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Авито'),
        ),
        migrations.AddField(
            model_name='avitomark',
            name='drom',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Drom'),
        ),
        migrations.AddField(
            model_name='avitomark',
            name='human_name',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Народное'),
        ),
        migrations.AddField(
            model_name='avitomark',
            name='teleph',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Телефония'),
        ),
    ]