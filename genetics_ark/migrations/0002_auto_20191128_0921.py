# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-11-28 09:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('genetics_ark', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CNV',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chrom', models.CharField(max_length=2)),
                ('start', models.PositiveIntegerField()),
                ('end', models.PositiveIntegerField()),
                ('type', models.CharField(max_length=15)),
            ],
            options={
                'db_table': 'cnv',
                'ordering': ['chrom', 'start', 'end', 'type'],
            },
        ),
        migrations.CreateModel(
            name='CNV_region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CNV', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.CNV')),
            ],
            options={
                'db_table': 'cnv_region',
            },
        ),
        migrations.CreateModel(
            name='CNV_target',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_file', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'cnv_target',
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=80)),
                ('date', models.DateTimeField()),
                ('comment', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'comment',
                'ordering': ['date', 'user'],
            },
        ),
        migrations.CreateModel(
            name='Decon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField(verbose_name='date of the run')),
                ('cnv_target', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.CNV_target')),
            ],
            options={
                'db_table': 'decon',
                'ordering': ['date', 'name'],
            },
        ),
        migrations.CreateModel(
            name='DeconAnalysis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('correlation', models.FloatField()),
                ('start_b', models.PositiveIntegerField()),
                ('end_b', models.PositiveIntegerField()),
                ('nb_exons', models.PositiveIntegerField()),
                ('BF', models.FloatField()),
                ('reads_expected', models.PositiveIntegerField()),
                ('reads_observed', models.PositiveIntegerField()),
                ('reads_ratio', models.FloatField()),
                ('CNV', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.CNV')),
                ('decon', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Decon')),
            ],
            options={
                'db_table': 'decon_analysis',
                'ordering': ['CNV', 'sample'],
            },
        ),
        migrations.AlterModelOptions(
            name='analysis',
            options={},
        ),
        migrations.AlterModelOptions(
            name='analysisvariant',
            options={},
        ),
        migrations.AlterModelOptions(
            name='annotation',
            options={},
        ),
        migrations.AlterModelOptions(
            name='gene',
            options={},
        ),
        migrations.AlterModelOptions(
            name='genepanel',
            options={},
        ),
        migrations.AlterModelOptions(
            name='meta',
            options={},
        ),
        migrations.AlterModelOptions(
            name='model',
            options={},
        ),
        migrations.AlterModelOptions(
            name='modelregion',
            options={},
        ),
        migrations.AlterModelOptions(
            name='panel',
            options={},
        ),
        migrations.AlterModelOptions(
            name='project',
            options={},
        ),
        migrations.AlterModelOptions(
            name='reference',
            options={},
        ),
        migrations.AlterModelOptions(
            name='region',
            options={},
        ),
        migrations.AlterModelOptions(
            name='runfolder',
            options={},
        ),
        migrations.AlterModelOptions(
            name='sample',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='samplepanel',
            options={},
        ),
        migrations.AlterModelOptions(
            name='transcript',
            options={'ordering': ['refseq']},
        ),
        migrations.AlterModelOptions(
            name='transcriptregion',
            options={},
        ),
        migrations.AlterModelOptions(
            name='variant',
            options={},
        ),
        migrations.AddField(
            model_name='deconanalysis',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Sample'),
        ),
        migrations.AddField(
            model_name='decon',
            name='runfolder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Runfolder'),
        ),
        migrations.AddField(
            model_name='comment',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Variant'),
        ),
        migrations.AddField(
            model_name='cnv_target',
            name='ref',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Reference'),
        ),
        migrations.AddField(
            model_name='cnv_region',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Region'),
        ),
        migrations.AddIndex(
            model_name='deconanalysis',
            index=models.Index(fields=['decon'], name='decon_analy_decon_i_99cef1_idx'),
        ),
        migrations.AddIndex(
            model_name='deconanalysis',
            index=models.Index(fields=['CNV'], name='decon_analy_CNV_id_01196a_idx'),
        ),
    ]