# Generated by Django 2.2.9 on 2020-03-02 22:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0066_auto_20200302_2314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mappingreleasecandidate',
            name='rules',
            field=models.ManyToManyField(blank=True, default=None, null=True, to='mapping.MappingReleaseCandidateRules'),
        ),
    ]