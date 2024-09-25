# Generated by Django 4.1.4 on 2024-07-09 14:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0020_call_repeat_call'),
    ]

    operations = [
        migrations.AlterField(
            model_name='call',
            name='num_redirect',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Номер переадресации'),
        ),
        migrations.AlterField(
            model_name='call',
            name='sip_primatel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='calls.sipprimatel', verbose_name='Sip'),
        ),
    ]
