# Generated by Django 4.1.4 on 2024-09-25 09:38

from django.db import migrations, models
import libs.services.models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0026_alter_call_duration_alter_call_num_to'),
    ]

    operations = [
        migrations.AlterField(
            model_name='call',
            name='moderation',
            field=models.CharField(blank=True, choices=[('Авто.ру', 'Авто.ру'), ('Авто.ру (Б)', 'Авто.ру (Б)'), ('Авто.ру БУ', 'Авто.ру БУ'), ('Заявка', 'Заявка'), ('Заявка А', 'Заявка А'), ('Заявка В', 'Заявка В'), ('Заявка С', 'Заявка С'), ('Дром', 'Дром'), ('Авито', 'Авито'), ('Авито БУ', 'Авито БУ'), ('Доп. ресурсы', 'Доп. ресурсы')], max_length=100, null=True, verbose_name='М'),
        ),
        migrations.AlterField(
            model_name='callpricesetting',
            name='moderation',
            field=libs.services.models.ChoiceArrayField(base_field=models.CharField(choices=[('Авто.ру', 'Авто.ру'), ('Авто.ру (Б)', 'Авто.ру (Б)'), ('Авто.ру БУ', 'Авто.ру БУ'), ('Заявка', 'Заявка'), ('Заявка А', 'Заявка А'), ('Заявка В', 'Заявка В'), ('Заявка С', 'Заявка С'), ('Дром', 'Дром'), ('Авито', 'Авито'), ('Авито БУ', 'Авито БУ'), ('Доп. ресурсы', 'Доп. ресурсы')], default=list, max_length=255), size=None, verbose_name='Модерация'),
        ),
    ]