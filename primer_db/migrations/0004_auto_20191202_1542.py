# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-12-02 15:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('primer_db', '0003_auto_20191202_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='primerdetails',
            name='last_date_used',
            field=models.DateField(blank=True, null=True),
        ),
    ]