# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-06-05 08:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('genetics_ark', '0006_auto_20190528_0905'),
    ]

    operations = [
        migrations.CreateModel(
            name='Deconexon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('chr', models.CharField(max_length=2)),
                ('start', models.PositiveIntegerField()),
                ('end', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='DeconexonCNV',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CNV', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='CNVs2Decongenes', to='genetics_ark.CNV')),
                ('deconexon', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='Decongenes2CNVs', to='genetics_ark.Deconexon')),
            ],
        ),
        migrations.RemoveField(
            model_name='decongenecnv',
            name='CNV',
        ),
        migrations.RemoveField(
            model_name='decongenecnv',
            name='decongene',
        ),
        migrations.DeleteModel(
            name='Decongene',
        ),
        migrations.DeleteModel(
            name='DecongeneCNV',
        ),
    ]