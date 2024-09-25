# Generated by Django 4.1.4 on 2024-08-08 09:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_account'),
        ('autoru', '0002_alter_autoruproduct_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autorucall',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounts.client', to_field='autoru_id', verbose_name='id клиента'),
        ),
        migrations.AlterField(
            model_name='autoruproduct',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.client', to_field='autoru_id', verbose_name='id клиента'),
        ),
    ]
