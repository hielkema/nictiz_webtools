# Generated by Django 2.2.9 on 2020-01-22 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('termspace', '0003_auto_20200122_1059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='termspacecomments',
            name='assignee',
            field=models.CharField(blank=True, default=None, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='termspacecomments',
            name='concept',
            field=models.CharField(blank=True, default=None, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='termspacecomments',
            name='folder',
            field=models.CharField(blank=True, default=None, max_length=600, null=True),
        ),
        migrations.AlterField(
            model_name='termspacecomments',
            name='fsn',
            field=models.CharField(blank=True, default=None, max_length=600, null=True),
        ),
        migrations.AlterField(
            model_name='termspacecomments',
            name='status',
            field=models.CharField(blank=True, default=None, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='termspacecomments',
            name='task_id',
            field=models.CharField(blank=True, default=None, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='termspacecomments',
            name='time',
            field=models.CharField(blank=True, default=None, max_length=300, null=True),
        ),
    ]