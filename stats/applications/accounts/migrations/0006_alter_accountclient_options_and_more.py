# Generated by Django 4.1.4 on 2024-08-08 10:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_alter_account_options_remove_account_active_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='accountclient',
            options={'verbose_name': 'Аккаунт-Клиент', 'verbose_name_plural': 'Аккаунты-Клиенты'},
        ),
        migrations.AlterModelTable(
            name='accountclient',
            table='accounts_account_client',
        ),
    ]
