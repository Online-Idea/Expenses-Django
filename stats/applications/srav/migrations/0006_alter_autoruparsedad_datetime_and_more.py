# Generated by Django 4.1.4 on 2024-01-09 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srav', '0005_remove_sravpivot_price_no_discount_diff_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autoruparsedad',
            name='datetime',
            field=models.DateTimeField(db_index=True, verbose_name='Дата и время'),
        ),
        migrations.AlterField(
            model_name='autoruparsedad',
            name='dealer',
            field=models.CharField(db_index=True, max_length=500, verbose_name='Имя дилера'),
        ),
        migrations.AlterField(
            model_name='autoruparsedad',
            name='region',
            field=models.CharField(db_index=True, max_length=500, verbose_name='Регион'),
        ),
    ]
