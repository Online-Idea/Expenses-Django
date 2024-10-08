# Generated by Django 4.1.4 on 2024-03-25 13:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('converter_id', models.IntegerField(unique=True, verbose_name='id в конвертере')),
                ('name', models.CharField(max_length=500, verbose_name='Название')),
                ('configuration', models.JSONField(verbose_name='Настройки')),
            ],
            options={
                'verbose_name': 'Конфигурация',
                'verbose_name_plural': 'Конфигурации',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ConverterLogsBotData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.CharField(max_length=500, verbose_name='id чата в телеграме')),
            ],
            options={
                'verbose_name': 'Логи конвертера',
                'verbose_name_plural': 'Логи конвертера',
                'db_table': 'autoconverter_converter_logs_bot_data',
                'ordering': ['chat_id'],
            },
        ),
        migrations.CreateModel(
            name='PhotoFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('folder', models.CharField(max_length=500, unique=True, verbose_name='Папка с фото')),
            ],
            options={
                'verbose_name': 'Папка с фото',
                'verbose_name_plural': 'Папки с фото',
                'db_table': 'autoconverter_photo_folder',
                'ordering': ['folder'],
            },
        ),
        migrations.CreateModel(
            name='StockFields',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, verbose_name='Название')),
                ('encoding', models.CharField(default='UTF-8', max_length=500, verbose_name='Кодировка')),
                ('car_tag', models.CharField(blank=True, max_length=500, null=True, verbose_name='Тег автомобиля')),
                ('modification_code', models.CharField(blank=True, max_length=500, null=True, verbose_name='Код модификации')),
                ('color_code', models.CharField(blank=True, max_length=500, null=True, verbose_name='Код цвета')),
                ('interior_code', models.CharField(blank=True, max_length=500, null=True, verbose_name='Код интерьера')),
                ('options_code', models.CharField(blank=True, help_text='\n        Если тег с детьми и нужно значение детей то пиши тег/дети, например options/option.\n        Если тег с детьми и из детей нужен атрибут то пиши тег/дети@атрибут, например options/option@code.\n        Если тег несколько раз повторяется и нужно значение то пиши тег, например option.\n        Если тег несколько раз повторяется и из него нужен атрибут то пиши тег@атрибут, например option@code.\n    ', max_length=500, null=True, verbose_name='Опции и пакеты')),
                ('price', models.CharField(blank=True, max_length=500, null=True, verbose_name='Цена')),
                ('year', models.CharField(blank=True, max_length=500, null=True, verbose_name='Год выпуска')),
                ('vin', models.CharField(blank=True, max_length=500, null=True, verbose_name='Исходный VIN')),
                ('id_from_client', models.CharField(blank=True, max_length=500, null=True, verbose_name='ID от клиента')),
                ('modification_explained', models.CharField(blank=True, max_length=500, null=True, verbose_name='Расш. модификации')),
                ('color_explained', models.CharField(blank=True, max_length=500, null=True, verbose_name='Расш. цвета')),
                ('interior_explained', models.CharField(blank=True, max_length=500, null=True, verbose_name='Расш. интерьера')),
                ('description', models.CharField(blank=True, max_length=500, null=True, verbose_name='Описание')),
                ('trade_in', models.CharField(blank=True, max_length=500, null=True, verbose_name='Трейд-ин')),
                ('credit', models.CharField(blank=True, max_length=500, null=True, verbose_name='Кредит')),
                ('insurance', models.CharField(blank=True, max_length=500, null=True, verbose_name='Страховка')),
                ('max_discount', models.CharField(blank=True, max_length=500, null=True, verbose_name='Максималка')),
                ('availability', models.CharField(blank=True, max_length=500, null=True, verbose_name='Наличие')),
                ('run', models.CharField(blank=True, max_length=500, null=True, verbose_name='Пробег')),
                ('images', models.CharField(blank=True, help_text='\n        Если тег с детьми и нужно значение детей то пиши тег/дети, например options/option.\n        Если тег с детьми и из детей нужен атрибут то пиши тег/дети@атрибут, например options/option@code.\n        Если тег несколько раз повторяется и нужно значение то пиши тег, например option.\n        Если тег несколько раз повторяется и из него нужен атрибут то пиши тег@атрибут, например option@code.\n    ', max_length=500, null=True, verbose_name='Фото клиента')),
            ],
            options={
                'verbose_name': 'Поля стока',
                'verbose_name_plural': 'Поля стоков',
                'db_table': 'autoconverter_stock_fields',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ConverterTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, verbose_name='Название')),
                ('stock_source', models.CharField(choices=[('Ссылка', 'Ссылка'), ('POST-запрос', 'POST-запрос')], max_length=500, verbose_name='Источник стока')),
                ('stock_url', models.URLField(blank=True, null=True, verbose_name='Ссылка стока')),
                ('stock_post_host', models.URLField(blank=True, null=True, verbose_name='POST-запрос Хост')),
                ('stock_post_login', models.CharField(blank=True, max_length=500, null=True, verbose_name='POST-запрос Логин')),
                ('stock_post_password', models.CharField(blank=True, max_length=500, null=True, verbose_name='POST-запрос Пароль')),
                ('active', models.BooleanField(default=True, verbose_name='Активна')),
                ('front', models.IntegerField(default=10, verbose_name='Начало')),
                ('back', models.IntegerField(default=10, verbose_name='Конец')),
                ('interior', models.IntegerField(blank=True, default=10, null=True, verbose_name='Фото интерьеров')),
                ('salon_only', models.BooleanField(default=False, verbose_name='Только фото салона')),
                ('template', models.URLField(verbose_name='Шаблон')),
                ('notifications_email', models.CharField(blank=True, max_length=500, null=True, verbose_name='Почта для уведомлений')),
                ('client', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Клиент')),
                ('configuration', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='autoconverter.configuration', verbose_name='Конфигурация')),
                ('photos_folder', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='autoconverter.photofolder', verbose_name='Папка с фото')),
                ('stock_fields', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='autoconverter.stockfields', verbose_name='Поля стока')),
            ],
            options={
                'verbose_name': 'Задача конвертера',
                'verbose_name_plural': 'Задачи конвертера',
                'db_table': 'autoconverter_converter_task',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ConverterFilter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(max_length=500, verbose_name='Поле')),
                ('condition', models.CharField(choices=[('in', 'содержит'), ('not in', 'не содержит'), ('==', 'равно'), ('!=', 'не равно'), ('>', 'больше'), ('<', 'меньше'), ('starts_with', 'начинается с'), ('not_starts_with', 'не начинается с'), ('ends_with', 'заканчивается на'), ('not_ends_with', 'не заканчивается на')], max_length=500, verbose_name='Условие')),
                ('value', models.CharField(help_text='Для фильтрации по нескольким значениям пиши каждое между `` и разделяй запятыми. Например: `E (W/S213)`, `CLS (C257)`', max_length=500, verbose_name='Значение')),
                ('converter_task', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='autoconverter.convertertask', verbose_name='Задача конвертера')),
            ],
            options={
                'verbose_name': 'Фильтр конвертера',
                'verbose_name_plural': 'Фильтры конвертера',
                'db_table': 'autoconverter_converter_filter',
                'ordering': ['field'],
            },
        ),
        migrations.CreateModel(
            name='ConverterExtraProcessing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('Сток', 'Сток'), ('Прайс', 'Прайс')], max_length=500, verbose_name='Источник')),
                ('price_column_to_change', models.CharField(max_length=500, verbose_name='Столбец прайса в котором менять')),
                ('new_value', models.CharField(help_text='Если одно значение для всех то пиши его, если из другого столбца то пиши имя столбцав формате: %col:"имя_столбца"', max_length=5000, verbose_name='Новое значение')),
                ('converter_task', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='autoconverter.convertertask', verbose_name='Задача конвертера')),
            ],
            options={
                'verbose_name': 'Обработка прайса',
                'verbose_name_plural': 'Обработка прайса',
                'db_table': 'autoconverter_converter_extra_processing',
            },
        ),
        migrations.CreateModel(
            name='Conditional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(help_text='\n        Если тег с детьми и нужно значение детей то пиши тег/дети, например options/option.\n        Если тег с детьми и из детей нужен атрибут то пиши тег/дети@атрибут, например options/option@code.\n        Если тег несколько раз повторяется и нужно значение то пиши тег, например option.\n        Если тег несколько раз повторяется и из него нужен атрибут то пиши тег@атрибут, например option@code.\n    ', max_length=500, verbose_name='Поле')),
                ('condition', models.CharField(choices=[('in', 'содержит'), ('not in', 'не содержит'), ('==', 'равно'), ('!=', 'не равно'), ('>', 'больше'), ('<', 'меньше'), ('starts_with', 'начинается с'), ('not_starts_with', 'не начинается с'), ('ends_with', 'заканчивается на'), ('not_ends_with', 'не заканчивается на')], max_length=500, verbose_name='Условие')),
                ('value', models.CharField(help_text='Для фильтрации по нескольким значениям пиши каждое между `` и разделяй запятыми. Например: `E (W/S213)`, `CLS (C257)`', max_length=500, verbose_name='Значение')),
                ('converter_extra_processing', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='autoconverter.converterextraprocessing')),
            ],
            options={
                'verbose_name': 'Условие',
                'verbose_name_plural': 'Условия',
            },
        ),
    ]
