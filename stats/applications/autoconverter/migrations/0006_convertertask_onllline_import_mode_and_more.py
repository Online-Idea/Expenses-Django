# Generated by Django 4.1.4 on 2024-03-15 08:18

from django.db import migrations, models
import libs.services.models


class Migration(migrations.Migration):

    dependencies = [
        ('autoconverter', '0005_convertertask_export_to_websites_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='convertertask',
            name='onllline_import_mode',
            field=models.CharField(blank=True, choices=[('Hide', 'Добавить объявления + скрытые'), ('AddDel', 'Добавить объявления + удалить'), ('Del', 'Удалить все + добавить'), ('Add', 'Добавить к имеющимся')], default=('AddDel', 'Добавить объявления + удалить'), max_length=255, null=True, verbose_name='Вариант импорта'),
        ),
        migrations.AddField(
            model_name='convertertask',
            name='price',
            field=models.URLField(blank=True, null=True, verbose_name='Прайс'),
        ),
        migrations.AlterField(
            model_name='convertertask',
            name='export_to_websites',
            field=libs.services.models.ChoiceArrayField(base_field=models.CharField(blank=True, choices=[('autoru', 'autoru'), ('avito', 'avito'), ('drom', 'drom')], default=list, max_length=255, null=True), blank=True, null=True, size=None, verbose_name='Экспорт на площадки'),
        ),
        migrations.AlterField(
            model_name='convertertask',
            name='template',
            field=models.URLField(blank=True, null=True, verbose_name='Шаблон'),
        ),
    ]
