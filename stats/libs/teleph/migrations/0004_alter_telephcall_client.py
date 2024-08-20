# Generated by Django 4.1.4 on 2024-08-08 09:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_account'),
        ('teleph', '0003_alter_telephcall_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telephcall',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.client', verbose_name='id клиента'),
        ),
    ]