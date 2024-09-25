# Generated by Django 4.1.4 on 2024-07-29 16:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('autoru', '0010_remove_autorucatalog_my_mark_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='autorugeneration',
            name='id_generation_autoru',
        ),
        migrations.RemoveField(
            model_name='autorumark',
            name='code_mark_autoru',
        ),
        migrations.RemoveField(
            model_name='autorumark',
            name='id_mark_autoru',
        ),
        migrations.RemoveField(
            model_name='autorumodel',
            name='id_folder_autoru',
        ),
        migrations.RemoveField(
            model_name='autorumodification',
            name='tech_param_id',
        ),
        migrations.AddField(
            model_name='autorugeneration',
            name='id_generation_level',
            field=models.IntegerField(default=0, verbose_name='Значение тега <generation> из xml-файла'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='autorumark',
            name='code_mark_level',
            field=models.CharField(default='', max_length=64, verbose_name='Значение тега <code> из xml-файла'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='autorumark',
            name='id_mark_level',
            field=models.IntegerField(blank=True, null=True, verbose_name='Значение атрибута "id" у тега <mark> из xml-файла'),
        ),
        migrations.AddField(
            model_name='autorumodel',
            name='code_model_level',
            field=models.CharField(default='', max_length=64, verbose_name='Значение тега <model> из xml-файла'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='autorumodel',
            name='id_folder',
            field=models.IntegerField(default=0, verbose_name='Значение атрибута "id" у тега <folder> из xml-файла'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='autorumodification',
            name='id_configuration_level',
            field=models.IntegerField(default=0, verbose_name='Значение тега <configuration_id> из xml-файла'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='autorumodification',
            name='id_tech_param_level',
            field=models.IntegerField(default=0, verbose_name='Значение тега <tech_param_id> из xml-файла'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='autorumodification',
            name='generation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modifications', to='autoru.autorugeneration', verbose_name='Поколение, к которой относится модификация'),
        ),
        migrations.AlterField(
            model_name='autorumodification',
            name='id_modification_autoru',
            field=models.IntegerField(verbose_name='Значение атрибута id у тега <modification> из xml файла'),
        ),
        migrations.AlterField(
            model_name='autorumodification',
            name='mark',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autoru.autorumark', verbose_name='Марка, к которой относится модификация'),
        ),
        migrations.AlterField(
            model_name='autorumodification',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autoru.autorumodel', verbose_name='Модель, к которой относится модификация'),
        ),
    ]
