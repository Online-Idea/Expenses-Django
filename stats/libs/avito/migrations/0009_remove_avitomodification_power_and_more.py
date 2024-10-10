# Generated by Django 4.1.4 on 2024-07-30 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('avito', '0008_alter_avitocomplectation_id_complectation_avito_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='avitomodification',
            name='power',
        ),
        migrations.AddField(
            model_name='avitomodification',
            name='power_hp',
            field=models.IntegerField(default=0, verbose_name='Мощность в лошадиных силах'),
        ),
        migrations.AddField(
            model_name='avitomodification',
            name='power_kw',
            field=models.IntegerField(default=0, verbose_name='Мощность в киловатах'),
        ),
    ]