# Generated by Django 4.1.4 on 2024-10-03 16:03

from django.db import migrations, models
import django.db.models.deletion
import libs.services.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0009_salon'),
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
            name='ConverterExtraProcessing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=True, verbose_name='Активно')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Заметка')),
            ],
            options={
                'verbose_name': 'Обработка прайса',
                'verbose_name_plural': 'Обработка прайса',
                'db_table': 'autoconverter_converter_extra_processing',
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
                ('active', models.BooleanField(default=True, verbose_name='Активна')),
                ('name', models.CharField(max_length=500, verbose_name='Название')),
                ('slug', models.SlugField(allow_unicode=True, max_length=500, verbose_name='Slug')),
                ('notifications_email', models.CharField(blank=True, max_length=500, null=True, verbose_name='Почта для уведомлений')),
                ('stock_source', models.CharField(choices=[('Ссылка', 'Ссылка'), ('POST-запрос', 'POST-запрос')], max_length=500, verbose_name='Источник стока')),
                ('stock_url', models.URLField(blank=True, null=True, verbose_name='Ссылка стока')),
                ('stock_post_host', models.URLField(blank=True, null=True, verbose_name='POST-запрос Хост')),
                ('stock_post_login', models.CharField(blank=True, max_length=500, null=True, verbose_name='POST-запрос Логин')),
                ('stock_post_password', models.CharField(blank=True, max_length=500, null=True, verbose_name='POST-запрос Пароль')),
                ('use_converter', models.BooleanField(default=True, help_text='Если в качестве стока используется наш прайс и конвертер не нужен для подставки фото, то выключи это. ', verbose_name='Использовать конвертер')),
                ('front', models.IntegerField(default=10, verbose_name='Начало')),
                ('back', models.IntegerField(default=10, verbose_name='Конец')),
                ('interior', models.IntegerField(blank=True, default=10, null=True, verbose_name='Фото интерьеров')),
                ('salon_only', models.BooleanField(default=False, verbose_name='Только фото салона')),
                ('template', models.URLField(blank=True, null=True, verbose_name='Шаблон')),
                ('price', models.URLField(blank=True, null=True, verbose_name='Прайс')),
                ('add_to_price', models.URLField(blank=True, help_text='Если нужно добавить объявления к прайсу после конвертера то укажи здесь ссылку на прайс сэтими объявлениями. Прайс размещай на наш ftp, в папке converter/имя_клиента/add/имя_файла.xlsx', null=True, verbose_name='Добавить к прайсу')),
                ('fill_vin', models.BooleanField(default=False, help_text='Добавляет в начало VIN знаки X если длина VIN меньше 17. Например VIN: 607130 станет XXXXXXXXXXX607130', verbose_name='Заполнить VIN знаками X')),
                ('change_vin', models.BooleanField(default=False, help_text='Меняет последние 6 цифр VIN на случайные. Если в последних 6 цифрах есть буква то меняет цифры после последней буквы.', verbose_name='Изменить VIN')),
                ('import_to_onllline', models.BooleanField(default=False, help_text='Если отмечено то после конвертера прайс будет импортирован в салон в базе onllline.ru', verbose_name='Импортировать в базу')),
                ('onllline_salon_to_import', models.IntegerField(blank=True, null=True, verbose_name='Номер салона onllline.ru')),
                ('onllline_import_mode', models.CharField(blank=True, choices=[('Hide', 'Добавить объявления + скрытые'), ('AddDel', 'Добавить объявления + удалить'), ('Del', 'Удалить все + добавить'), ('Add', 'Добавить к имеющимся')], default=('AddDel', 'Добавить объявления + удалить'), max_length=255, null=True, verbose_name='Вариант импорта')),
                ('onllline_import_options', libs.services.models.ChoiceArrayField(base_field=models.CharField(blank=True, choices=[('-----', '-----'), ('save_images', 'Сохранить названия фото'), ('save_services', 'Оставлять услуги'), ('ad_add_vin', 'Присваивать ВИН модели')], default=list, max_length=255, null=True), blank=True, help_text='Для выбора нескольких удерживай Ctrl', null=True, size=None, verbose_name='Опции импорта')),
                ('onllline_import_multiply_price', models.IntegerField(blank=True, null=True, verbose_name='Размножить сток')),
                ('export_to_onllline', models.BooleanField(default=False, help_text='Если отмечено то после импорта выгрузит на площадки по списку из Экспорт на площадки', verbose_name='Экспортировать на площадки')),
                ('export_to_websites', libs.services.models.ChoiceArrayField(base_field=models.CharField(blank=True, choices=[('-----', '-----'), ('autoru', 'auto.ru (новый каталог)'), ('avito', 'avito.ru'), ('drom', 'drom.ru'), ('yandexYml', 'Yandex Market'), ('110km', '110km.ru'), ('automobile', 'am.ru'), ('comautoru', 'auto.ru (ком. транспорт)'), ('navigator', 'autonavigator.ru'), ('avto25', 'avto25.ru'), ('bibika', 'bibika.ru'), ('carcopy', 'carcopy.ru'), ('car', 'car.ru'), ('cars', 'cars.ru'), ('carsguru', 'carsguru.ru'), ('clubrussia', 'Club Russia'), ('dmir', 'dmir.ru'), ('irr2', 'irr.ru'), ('quto', 'quto.ru'), ('usedcars', 'usedcars.ru'), ('yandexYml', 'yandex.yml'), ('vk', 'vk.com'), ('csv', 'файл для Excel')], default=list, max_length=255, null=True), blank=True, help_text='Для выбора нескольких удерживай Ctrl', null=True, size=None, verbose_name='Экспорт на площадки')),
                ('autoru_xml', models.URLField(blank=True, null=True, verbose_name='Авто.ру xml')),
                ('client', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.client', verbose_name='Клиент')),
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
                ('condition', models.CharField(choices=[('in', 'содержит'), ('not in', 'не содержит'), ('==', 'равно'), ('!=', 'не равно'), ('>', 'больше'), ('>=', 'больше либо равно'), ('<', 'меньше'), ('<=', 'меньше либо равно'), ('starts_with', 'начинается с'), ('not_starts_with', 'не начинается с'), ('ends_with', 'заканчивается на'), ('not_ends_with', 'не заканчивается на')], default=('==', 'равно'), max_length=500, verbose_name='Условие')),
                ('value', models.CharField(help_text='Для фильтрации по нескольким значениям пиши каждое между `` и разделяй запятыми. Например: `E (W/S213)`, `CLS (C257)`. Для фильтрации по пустым значениям выбирай в условии не равно, в значении ""', max_length=500, verbose_name='Значение')),
                ('active', models.BooleanField(default=True, verbose_name='Активно')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Заметка')),
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
            name='ConverterExtraProcessingNewChanges',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_column_to_change', models.CharField(max_length=500, verbose_name='Столбец прайса в котором менять')),
                ('new_value', models.TextField(blank=True, help_text='Если одно значение для всех то пиши его, если из другого столбца то пиши имя столбцав формате: %col:"имя_столбца"', max_length=10000, null=True, verbose_name='Новое значение')),
                ('change_type', models.CharField(choices=[('Полностью', 'Полностью'), ('Добавить в начало', 'Добавить в начало'), ('Добавить в конец', 'Добавить в конец')], default=('Полностью', 'Полностью'), max_length=255, verbose_name='Как заменять')),
                ('converter_extra_processing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autoconverter.converterextraprocessing', verbose_name='Обработка прайса')),
            ],
            options={
                'verbose_name': 'Обработка прайса новое значение',
                'verbose_name_plural': 'Обработка прайса новые значения',
                'db_table': 'autoconverter_converter_extra_processing_new_changes',
            },
        ),
        migrations.AddField(
            model_name='converterextraprocessing',
            name='converter_task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='autoconverter.convertertask', verbose_name='Задача конвертера'),
        ),
        migrations.CreateModel(
            name='Conditional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('Сток', 'Сток'), ('Прайс', 'Прайс')], max_length=500, verbose_name='Источник')),
                ('field', models.CharField(help_text='\n        Если тег с детьми и нужно значение детей то пиши тег/дети, например options/option.\n        Если тег с детьми и из детей нужен атрибут то пиши тег/дети@атрибут, например options/option@code.\n        Если тег несколько раз повторяется и нужно значение то пиши тег, например option.\n        Если тег несколько раз повторяется и из него нужен атрибут то пиши тег@атрибут, например option@code.\n    ', max_length=500, verbose_name='Поле')),
                ('condition', models.CharField(choices=[('in', 'содержит'), ('not in', 'не содержит'), ('==', 'равно'), ('!=', 'не равно'), ('>', 'больше'), ('>=', 'больше либо равно'), ('<', 'меньше'), ('<=', 'меньше либо равно'), ('starts_with', 'начинается с'), ('not_starts_with', 'не начинается с'), ('ends_with', 'заканчивается на'), ('not_ends_with', 'не заканчивается на')], default=('==', 'равно'), max_length=500, verbose_name='Условие')),
                ('value', models.CharField(help_text='Для фильтрации по нескольким значениям пиши каждое между `` и разделяй запятыми. Например: `E (W/S213)`, `CLS (C257)`. Для фильтрации по пустым значениям выбирай в условии не равно, в значении ""', max_length=5000, verbose_name='Значение')),
                ('converter_extra_processing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autoconverter.converterextraprocessing')),
            ],
            options={
                'verbose_name': 'Условие',
                'verbose_name_plural': 'Условия',
            },
        ),
    ]
