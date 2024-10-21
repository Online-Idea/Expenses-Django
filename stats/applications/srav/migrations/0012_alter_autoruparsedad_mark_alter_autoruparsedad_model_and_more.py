# Generated by Django 4.1.4 on 2024-10-11 12:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0013_alter_model_options_model_unique_mark_model'),
        ('srav', '0011_alter_autoruparsedad_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autoruparsedad',
            name='mark',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mainapp.mark'),
        ),
        migrations.AlterField(
            model_name='autoruparsedad',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mainapp.model'),
        ),
        migrations.AlterField(
            model_name='uniqueautoruparsedadmark',
            name='mark',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='mainapp.mark', verbose_name='Марка'),
        ),
    ]
