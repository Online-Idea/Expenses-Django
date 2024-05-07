# Generated by Django 4.1.4 on 2024-05-06 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0008_remove_complectation_autoru_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='generation',
            name='autoru',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Авто.ру'),
        ),
        migrations.AddField(
            model_name='generation',
            name='avito',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Авито'),
        ),
        migrations.AddField(
            model_name='generation',
            name='drom',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Drom'),
        ),
        migrations.AddField(
            model_name='generation',
            name='human_name',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Народное'),
        ),
        migrations.AddField(
            model_name='generation',
            name='teleph',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Телефония'),
        ),
        migrations.AddField(
            model_name='mark',
            name='autoru',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Авто.ру'),
        ),
        migrations.AddField(
            model_name='mark',
            name='avito',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Авито'),
        ),
        migrations.AddField(
            model_name='mark',
            name='drom',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Drom'),
        ),
        migrations.AddField(
            model_name='mark',
            name='human_name',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Народное'),
        ),
        migrations.AddField(
            model_name='mark',
            name='teleph',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Телефония'),
        ),
        migrations.AddField(
            model_name='model',
            name='autoru',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Авто.ру'),
        ),
        migrations.AddField(
            model_name='model',
            name='avito',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Авито'),
        ),
        migrations.AddField(
            model_name='model',
            name='drom',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Drom'),
        ),
        migrations.AddField(
            model_name='model',
            name='human_name',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Народное'),
        ),
        migrations.AddField(
            model_name='model',
            name='teleph',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Телефония'),
        ),
    ]