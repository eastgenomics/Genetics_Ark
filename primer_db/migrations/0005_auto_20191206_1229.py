# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-12-06 12:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('primer_db', '0004_auto_20191202_1542'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coordinates',
            name='reference',
        ),
        migrations.AddField(
            model_name='primerdetails',
            name='strand',
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
    ]