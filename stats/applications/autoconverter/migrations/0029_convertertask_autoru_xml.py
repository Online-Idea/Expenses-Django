# Generated by Django 4.1.4 on 2024-09-26 08:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoconverter', '0028_alter_conditional_condition_alter_conditional_value_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='convertertask',
            name='autoru_xml',
            field=models.URLField(blank=True, null=True, verbose_name='Авто.ру xml'),
        ),
    ]