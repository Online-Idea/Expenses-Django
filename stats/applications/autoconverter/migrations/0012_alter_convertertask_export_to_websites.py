# Generated by Django 4.1.4 on 2024-03-18 09:10

from django.db import migrations, models
import libs.services.models


class Migration(migrations.Migration):

    dependencies = [
        ('autoconverter', '0011_alter_convertertask_export_to_websites'),
    ]

    operations = [
        migrations.AlterField(
            model_name='convertertask',
            name='export_to_websites',
            field=libs.services.models.ChoiceArrayField(base_field=models.CharField(blank=True, choices=[('-----', '-----'), ('autoru', 'auto.ru (новый каталог)'), ('avito', 'avito.ru'), ('drom', 'drom.ru'), ('yandexYml', 'Yandex Market'), ('110km', '110km.ru'), ('automobile', 'am.ru'), ('comautoru', 'auto.ru (ком. транспорт)'), ('navigator', 'autonavigator.ru'), ('avto25', 'avto25.ru'), ('bibika', 'bibika.ru'), ('carcopy', 'carcopy.ru'), ('car', 'car.ru'), ('cars', 'cars.ru'), ('carsguru', 'carsguru.ru'), ('clubrussia', 'Club Russia'), ('dmir', 'dmir.ru'), ('irr2', 'irr.ru'), ('quto', 'quto.ru'), ('usedcars', 'usedcars.ru'), ('yandexYml', 'yandex.yml'), ('vk', 'vk.com'), ('csv', 'файл для Excel')], default=list, max_length=255, null=True), blank=True, null=True, size=None, verbose_name='Экспорт на площадки'),
        ),
    ]
