# Generated by Django 4.1.4 on 2023-12-05 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0004_alter_ad_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ad',
            name='description',
            field=models.CharField(blank=True, max_length=10500, verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='ad',
            name='photo',
            field=models.CharField(blank=True, max_length=10500, verbose_name='Ссылка на фото'),
        ),
    ]