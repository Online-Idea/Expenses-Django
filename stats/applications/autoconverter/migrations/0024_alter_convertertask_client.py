# Generated by Django 4.1.4 on 2024-08-08 09:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_account'),
        ('autoconverter', '0023_converterextraprocessing_active_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='convertertask',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.client', verbose_name='Клиент'),
        ),
    ]
