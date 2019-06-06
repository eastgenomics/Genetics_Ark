# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-06-06 07:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('genetics_ark', '0007_auto_20190605_0825'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deconsample',
            name='decon',
        ),
        migrations.RemoveField(
            model_name='deconsample',
            name='sample',
        ),
        migrations.AddField(
            model_name='deconcnv',
            name='sample',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Sample'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='DeconSample',
        ),
    ]
