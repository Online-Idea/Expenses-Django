# Generated by Django 4.1.4 on 2024-07-22 18:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('avito', '0007_alter_avitocomplectation_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='avitocomplectation',
            name='id_complectation_avito',
            field=models.IntegerField(verbose_name='id комплектации из xml файла авито'),
        ),
        migrations.AlterField(
            model_name='avitocomplectation',
            name='modification',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='complectations', to='avito.avitomodification', verbose_name='Ссылка на соответствующую модификацию автомобиля'),
        ),
        migrations.AlterField(
            model_name='avitogeneration',
            name='id_generation_avito',
            field=models.IntegerField(verbose_name='id поколения из xml файла авито'),
        ),
        migrations.AlterField(
            model_name='avitogeneration',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generations', to='avito.avitomodel', verbose_name='Ссылка на соответствующую модель автомобиля'),
        ),
        migrations.AlterField(
            model_name='avitomark',
            name='id_mark_avito',
            field=models.IntegerField(verbose_name='id марки из xml файла авито'),
        ),
        migrations.AlterField(
            model_name='avitomodel',
            name='id_model_avito',
            field=models.IntegerField(verbose_name='id модели из xml файла авито'),
        ),
        migrations.AlterField(
            model_name='avitomodel',
            name='mark',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='models', to='avito.avitomark', verbose_name='Ссылка на соответствующую марку автомобиля'),
        ),
        migrations.AlterField(
            model_name='avitomodification',
            name='battery_capacity',
            field=models.FloatField(blank=True, null=True, verbose_name='Ёмкость батареи'),
        ),
    ]