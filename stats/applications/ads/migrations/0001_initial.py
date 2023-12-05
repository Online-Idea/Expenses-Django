# Generated by Django 4.1.4 on 2023-12-05 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Salon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('price_url', models.CharField(max_length=2000, verbose_name='Ссылка на прайс')),
                ('datetime_updated', models.DateTimeField(verbose_name='Время последнего обновления')),
                ('client', models.ManyToManyField(to='services.client')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
