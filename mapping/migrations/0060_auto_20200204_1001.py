# Generated by Django 2.2.9 on 2020-02-04 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0059_auto_20200131_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mappingproject',
            name='title',
            field=models.CharField(max_length=150),
        ),
    ]
