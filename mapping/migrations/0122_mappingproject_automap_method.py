# Generated by Django 3.1.7 on 2021-04-22 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0121_mappingproject_automap_valueset'),
    ]

    operations = [
        migrations.AddField(
            model_name='mappingproject',
            name='automap_method',
            field=models.CharField(blank=True, default='MML', max_length=50, null=True),
        ),
    ]