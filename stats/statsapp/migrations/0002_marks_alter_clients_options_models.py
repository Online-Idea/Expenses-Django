# Generated by Django 4.1.2 on 2022-10-23 19:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('statsapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Marks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mark', models.CharField(max_length=255, unique=True, verbose_name='Марка')),
                ('teleph', models.CharField(max_length=255, null=True, unique=True, verbose_name='Телефония')),
                ('autoru', models.CharField(max_length=255, null=True, unique=True, verbose_name='Авто.ру')),
                ('avito', models.CharField(max_length=255, null=True, unique=True, verbose_name='Авито')),
                ('drom', models.CharField(max_length=255, null=True, unique=True, verbose_name='Drom')),
                ('human_name', models.CharField(max_length=255, null=True, verbose_name='Народное')),
            ],
            options={
                'verbose_name': 'Марки',
                'verbose_name_plural': 'Марки',
                'ordering': ['mark'],
            },
        ),
        migrations.AlterModelOptions(
            name='clients',
            options={'ordering': ['name'], 'verbose_name': 'Клиенты', 'verbose_name_plural': 'Клиенты'},
        ),
        migrations.CreateModel(
            name='Models',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.CharField(max_length=255, verbose_name='Модель')),
                ('teleph', models.CharField(max_length=255, verbose_name='Телефония')),
                ('autoru', models.CharField(max_length=255, verbose_name='Авто.ру')),
                ('avito', models.CharField(max_length=255, verbose_name='Авито')),
                ('drom', models.CharField(max_length=255, verbose_name='Drom')),
                ('human_name', models.CharField(max_length=255, verbose_name='Народное')),
                ('mark_id', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='statsapp.marks', verbose_name='Марка')),
            ],
            options={
                'verbose_name': 'Модели',
                'verbose_name_plural': 'Модели',
                'ordering': ['model'],
            },
        ),
    ]
