# Generated by Django 4.1.4 on 2024-03-11 10:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoconverter', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='converterextraprocessing',
            name='change_type',
            field=models.CharField(choices=[('Полностью', 'Полностью'), ('Добавить в начало', 'Добавить в начало'), ('Добавить в конец', 'Добавить в конец')], default=('Полностью', 'Полностью'), max_length=255, verbose_name='Как заменять'),
        ),
    ]