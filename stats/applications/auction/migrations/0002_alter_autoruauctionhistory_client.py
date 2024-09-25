# Generated by Django 4.1.4 on 2024-08-08 09:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_account'),
        ('auction', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autoruauctionhistory',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.client'),
        ),
    ]
