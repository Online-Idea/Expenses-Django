# Generated by Django 4.1.4 on 2024-05-23 10:37

from django.db import migrations, models
import libs.services.models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0009_alter_callpricesetting_moderation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='callpricesetting',
            name='moderation',
            field=libs.services.models.ChoiceArrayField(base_field=models.CharField(choices=[('М', 'М'), ('М(З)', 'М(З)'), ('М(Б)', 'М(Б)'), ('БУ', 'БУ'), ('Авто.ру БУ', 'Авто.ру БУ'), ('Заявка', 'Заявка'), ('Дром', 'Дром'), ('Авито', 'Авито'), ('Авито БУ', 'Авито БУ'), ('Запас', 'Запас'), ('Доп. ресурсы', 'Доп. ресурсы')], default=list, max_length=255), default='{М}', size=None, verbose_name='Модерация'),
            preserve_default=False,
        ),
    ]