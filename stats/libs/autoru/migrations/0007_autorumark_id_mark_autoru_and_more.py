# Generated by Django 4.1.4 on 2024-05-23 14:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('autoru', '0006_alter_autorumodel_id_folder_autoru'),
    ]

    operations = [
        migrations.AddField(
            model_name='autorumark',
            name='id_mark_autoru',
            field=models.IntegerField(default=0, verbose_name='Атрибут id у тега <mark> из xml файла'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='autorucomplectation',
            name='modification',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='complectations', to='autoru.autorumodification', verbose_name='Комплектация'),
        ),
        migrations.AlterField(
            model_name='autorugeneration',
            name='id_generation_autoru',
            field=models.IntegerField(verbose_name='атрибут id у тега <generation> из xml файла'),
        ),
        migrations.AlterField(
            model_name='autorumodel',
            name='id_folder_autoru',
            field=models.IntegerField(verbose_name='Атрибут id у тега <folder> из xml файла'),
        ),
        migrations.AlterField(
            model_name='autorumodification',
            name='id_modification_autoru',
            field=models.IntegerField(verbose_name='атрибут id у тега <modification> из xml файла'),
        ),
    ]
