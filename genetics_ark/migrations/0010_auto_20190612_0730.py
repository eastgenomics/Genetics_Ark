# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-06-12 07:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('genetics_ark', '0009_auto_20190606_1143'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=80)),
                ('date', models.DateTimeField()),
                ('comment', models.CharField(max_length=200)),
            ],
        ),
        migrations.RemoveField(
            model_name='variant',
            name='comment',
        ),
        migrations.AddField(
            model_name='comment',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Variant'),
        ),
    ]
