
# Generated by Django 4.1.4 on 2024-04-04 11:24


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoconverter', '0014_convertertask_add_to_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='convertertask',
            name='add_to_price',
            field=models.URLField(blank=True, help_text='Если нужно добавить объявления к прайсу после конвертера то укажи здесь ссылку на прайс сэтими объявлениями. Прайс размещай на наш ftp, в папке converter/имя_клиента/add/имя_файла.xlsx', null=True, verbose_name='Добавить к прайсу'),
        ),
    ]
