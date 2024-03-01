# Generated by Django 4.1.4 on 2023-12-25 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0007_alter_ad_vin'),
    ]

    operations = [
        migrations.AddField(
            model_name='ad',
            name='availability',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='Наличие'),
        ),
        migrations.AddField(
            model_name='ad',
            name='color_code',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Код цвета'),
        ),
        migrations.AddField(
            model_name='ad',
            name='condition',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Состояние машины'),
        ),
        migrations.AddField(
            model_name='ad',
            name='configuration_autoru',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Комплектация авто.ру'),
        ),
        migrations.AddField(
            model_name='ad',
            name='configuration_codes',
            field=models.CharField(blank=True, max_length=1024, null=True, verbose_name='Коды опций комплектации'),
        ),
        migrations.AddField(
            model_name='ad',
            name='credit',
            field=models.IntegerField(blank=True, null=True, verbose_name='Кредит'),
        ),
        migrations.AddField(
            model_name='ad',
            name='currency',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Валюта'),
        ),
        migrations.AddField(
            model_name='ad',
            name='drive',
            field=models.CharField(blank=True, max_length=32, verbose_name='Привод'),
        ),
        migrations.AddField(
            model_name='ad',
            name='engine_capacity',
            field=models.IntegerField(blank=True, null=True, verbose_name='Объём двигателя'),
        ),
        migrations.AddField(
            model_name='ad',
            name='engine_type',
            field=models.CharField(blank=True, max_length=32, verbose_name='Тип двигателя'),
        ),
        migrations.AddField(
            model_name='ad',
            name='id_client',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='ID от клиента'),
        ),
        migrations.AddField(
            model_name='ad',
            name='id_configuration_autoru',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID комплектации на авто.ру'),
        ),
        migrations.AddField(
            model_name='ad',
            name='id_model_autoru',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID модели на авто.ру'),
        ),
        migrations.AddField(
            model_name='ad',
            name='id_modification_autoru',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID модификации на авто.ру'),
        ),
        migrations.AddField(
            model_name='ad',
            name='insurance',
            field=models.IntegerField(blank=True, null=True, verbose_name='Страховка'),
        ),
        migrations.AddField(
            model_name='ad',
            name='interior_code',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Код интерьера'),
        ),
        migrations.AddField(
            model_name='ad',
            name='max_discount',
            field=models.IntegerField(blank=True, null=True, verbose_name='Максимальная скидка'),
        ),
        migrations.AddField(
            model_name='ad',
            name='modification_autoru',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Модификация авто.ру'),
        ),
        migrations.AddField(
            model_name='ad',
            name='modification_code',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='Код модификации'),
        ),
        migrations.AddField(
            model_name='ad',
            name='original_vin',
            field=models.CharField(blank=True, max_length=17, null=True, verbose_name='Исходный VIN'),
        ),
        migrations.AddField(
            model_name='ad',
            name='power',
            field=models.IntegerField(default=0, verbose_name='Мощность'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ad',
            name='price_nds',
            field=models.CharField(blank=True, max_length=8, null=True, verbose_name='Цена c НДС'),
        ),
        migrations.AddField(
            model_name='ad',
            name='run',
            field=models.IntegerField(blank=True, null=True, verbose_name='Пробег'),
        ),
        migrations.AddField(
            model_name='ad',
            name='status',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Статус продажи'),
        ),
        migrations.AddField(
            model_name='ad',
            name='stickers_autoru',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='Стикеры авто.ру'),
        ),
        migrations.AddField(
            model_name='ad',
            name='telephone',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Номер телефона'),
        ),
        migrations.AddField(
            model_name='ad',
            name='trade_in',
            field=models.IntegerField(blank=True, null=True, verbose_name='Трейд-ин'),
        ),
        migrations.AddField(
            model_name='ad',
            name='transmission',
            field=models.CharField(blank=True, max_length=16, verbose_name='Коробка передач'),
        ),
        migrations.AddField(
            model_name='ad',
            name='video',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='Ссылка на видео'),
        ),
        migrations.AlterField(
            model_name='ad',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата создания и размещения'),
        ),
        migrations.AlterField(
            model_name='ad',
            name='vin',
            field=models.CharField(blank=True, max_length=17, null=True, verbose_name='VIN'),
        ),
    ]