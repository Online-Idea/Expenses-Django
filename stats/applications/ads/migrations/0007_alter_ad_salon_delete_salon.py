# Generated by Django 4.1.4 on 2024-09-30 11:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_salon'),
        ('ads', '0006_merge_20240926_1739'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ad',
            name='salon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ads', to='accounts.salon', verbose_name='Салон, которому принадлежит объявление'),
        ),
        migrations.DeleteModel(
            name='Salon',
        ),
    ]