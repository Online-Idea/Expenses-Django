# Generated by Django 4.1.4 on 2024-09-25 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoconverter', '0027_convertertask_fill_vin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conditional',
            name='condition',
            field=models.CharField(choices=[('in', 'содержит'), ('not in', 'не содержит'), ('==', 'равно'), ('!=', 'не равно'), ('>', 'больше'), ('>=', 'больше либо равно'), ('<', 'меньше'), ('<=', 'меньше либо равно'), ('starts_with', 'начинается с'), ('not_starts_with', 'не начинается с'), ('ends_with', 'заканчивается на'), ('not_ends_with', 'не заканчивается на')], default=('==', 'равно'), max_length=500, verbose_name='Условие'),
        ),
        migrations.AlterField(
            model_name='conditional',
            name='value',
            field=models.CharField(help_text='Для фильтрации по нескольким значениям пиши каждое между `` и разделяй запятыми. Например: `E (W/S213)`, `CLS (C257)`. Для фильтрации по пустым значениям выбирай в условии не равно, в значении ""', max_length=5000, verbose_name='Значение'),
        ),
        migrations.AlterField(
            model_name='converterfilter',
            name='condition',
            field=models.CharField(choices=[('in', 'содержит'), ('not in', 'не содержит'), ('==', 'равно'), ('!=', 'не равно'), ('>', 'больше'), ('>=', 'больше либо равно'), ('<', 'меньше'), ('<=', 'меньше либо равно'), ('starts_with', 'начинается с'), ('not_starts_with', 'не начинается с'), ('ends_with', 'заканчивается на'), ('not_ends_with', 'не заканчивается на')], default=('==', 'равно'), max_length=500, verbose_name='Условие'),
        ),
        migrations.AlterField(
            model_name='converterfilter',
            name='value',
            field=models.CharField(help_text='Для фильтрации по нескольким значениям пиши каждое между `` и разделяй запятыми. Например: `E (W/S213)`, `CLS (C257)`. Для фильтрации по пустым значениям выбирай в условии не равно, в значении ""', max_length=500, verbose_name='Значение'),
        ),
    ]
