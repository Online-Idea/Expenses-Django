# Generated by Django 4.1.4 on 2024-08-30 13:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0026_alter_call_duration_alter_call_num_to'),
        ('autoru', '0003_alter_autorucall_client_alter_autoruproduct_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='autorucall',
            name='call',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='calls.call', verbose_name='Звонок'),
        ),
    ]
