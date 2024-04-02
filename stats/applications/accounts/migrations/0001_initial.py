# Generated by Django 4.1.4 on 2024-03-25 13:05

import django.contrib.auth.validators
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('name', models.CharField(max_length=255, verbose_name='Имя')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('slug', models.SlugField(allow_unicode=True, max_length=300, verbose_name='Slug')),
                ('manager', models.CharField(max_length=255, null=True, verbose_name='Менеджер')),
                ('active', models.BooleanField(default='1', verbose_name='Активен')),
                ('charge_type', models.CharField(choices=[('звонки', 'звонки'), ('комиссия процент', 'комиссия процент'), ('комиссия сумма', 'комиссия сумма')], default='звонки', max_length=255, verbose_name='Тип')),
                ('commission_size', models.FloatField(blank=True, null=True, verbose_name='Размер комиссии')),
                ('teleph_id', models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name='Имя в телефонии')),
                ('autoru_id', models.IntegerField(blank=True, null=True, unique=True, verbose_name='id авто.ру')),
                ('autoru_name', models.CharField(blank=True, max_length=500, null=True, verbose_name='Имя на авто.ру')),
                ('avito_id', models.IntegerField(blank=True, null=True, unique=True, verbose_name='id авито')),
                ('drom_id', models.IntegerField(blank=True, null=True, unique=True, verbose_name='id drom')),
                ('is_staff', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Клиент',
                'verbose_name_plural': 'Клиенты',
                'ordering': ['name'],
            },
        ),
    ]
