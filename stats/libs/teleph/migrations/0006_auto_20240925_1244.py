# Generated by Django 4.1.4 on 2024-09-25 09:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teleph', '0005_rename_target_telephcall_num_to'),
    ]

    operations = [
        migrations.RenameField(
            model_name='TelephCall',
            old_name='num_to',
            new_name='target',
        )
    ]
