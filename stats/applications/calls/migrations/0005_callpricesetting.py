# Generated by Django 4.1.4 on 2024-05-21 09:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_model_unique_mark_model'),
        ('calls', '0004_clientprimatel_client'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallPriceSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('charge_type', models.CharField(choices=[('Общая', 'Общая'), ('Модерация', 'Модерация'), ('Марка', 'Марка'), ('Модель', 'Модель')], max_length=255, verbose_name='Тип')),
                ('price', models.IntegerField(verbose_name='Стоимость звонка')),
                ('moderation', models.CharField(choices=[('М', 'М'), ('М(З)', 'М(З)'), ('М(Б)', 'М(Б)'), ('БУ', 'БУ'), ('Авто.ру БУ', 'Авто.ру БУ'), ('Заявка', 'Заявка'), ('Дром', 'Дром'), ('Авито', 'Авито'), ('Авито БУ', 'Авито БУ'), ('Запас', 'Запас'), ('Доп. ресурсы', 'Доп. ресурсы')], max_length=255, verbose_name='Модерация')),
                ('client_primatel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='call_price_settings', to='calls.clientprimatel', verbose_name='Клиент Примател')),
                ('mark', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='services.mark', verbose_name='Марка')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='services.model', verbose_name='Модель')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]