# Generated by Django 2.2.12 on 2020-05-13 11:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('postcoordination', '0004_template_root_concept'),
    ]

    operations = [
        migrations.AlterField(
            model_name='template',
            name='root_concept',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='rootAttribute', to='postcoordination.attributeValue'),
        ),
    ]