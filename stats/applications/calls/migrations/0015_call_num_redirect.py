# Generated by Django 4.1.4 on 2024-05-28 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0014_delete_ourphonenumbers'),
    ]

    operations = [
        migrations.AddField(
            model_name='call',
            name='num_redirect',
            field=models.CharField(default='default', max_length=30, verbose_name='Номер переадресации'),
            preserve_default=False,
        ),
    ]