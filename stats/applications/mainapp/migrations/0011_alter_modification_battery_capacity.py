# Generated by Django 4.1.4 on 2024-07-22 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0010_alter_complectation_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modification',
            name='battery_capacity',
            field=models.FloatField(blank=True, null=True, verbose_name='Ёмкость батареи'),
        ),
    ]
