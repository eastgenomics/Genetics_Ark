# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-07-17 08:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('primer_db', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='buffer',
            name='name',
        ),
        migrations.AddField(
            model_name='buffer',
            name='buffer',
            field=models.CharField(default=None, max_length=200),
            preserve_default=False,
        ),
    ]