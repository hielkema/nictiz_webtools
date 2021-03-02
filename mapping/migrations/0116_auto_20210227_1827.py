# Generated by Django 3.1.7 on 2021-02-27 17:27

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0115_auto_20210129_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mappingcodesystemcomponent',
            name='component_extra_dict',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='mappingcodesystemcomponent',
            name='descriptions',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='mappingeclpart',
            name='result',
            field=models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
        migrations.AlterField(
            model_name='mappingeclpartexclusion',
            name='components',
            field=models.JSONField(blank=True, default=list, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
        migrations.AlterField(
            model_name='mappingproject',
            name='categories',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
        migrations.AlterField(
            model_name='mappingproject',
            name='tags',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='mappingreleasecandidatefhirconceptmap',
            name='data',
            field=models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterField(
            model_name='mappingreleasecandidaterules',
            name='mapspecifies',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='mappingreleasecandidaterules',
            name='static_source_component',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='mappingreleasecandidaterules',
            name='static_target_component',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]
