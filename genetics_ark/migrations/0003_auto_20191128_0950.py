# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-11-28 09:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('genetics_ark', '0002_auto_20191128_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='reference',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Reference'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='runfolder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Runfolder'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='sample',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Sample'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='analysisvariant',
            name='analysis',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Analysis'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='analysisvariant',
            name='variant',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Variant'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='annotation',
            name='transcript',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Transcript'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='annotation',
            name='variant',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Variant'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='genepanel',
            name='gene',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Gene'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='genepanel',
            name='panel',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Panel'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelregion',
            name='model',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Model'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelregion',
            name='region',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Region'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='region',
            name='reference',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Reference'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sample',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Project'),
        ),
        migrations.AddField(
            model_name='samplepanel',
            name='sample',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Sample'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transcript',
            name='gene',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Gene'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transcriptregion',
            name='region',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Region'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transcriptregion',
            name='transcript',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Transcript'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='variant',
            name='reference',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.DO_NOTHING, to='genetics_ark.Reference'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='analysis',
            unique_together=set([('sample', 'runfolder', 'reference')]),
        ),
        migrations.AlterUniqueTogether(
            name='annotation',
            unique_together=set([('variant', 'transcript')]),
        ),
        migrations.RemoveField(
            model_name='variant',
            name='comment',
        ),
        migrations.AlterUniqueTogether(
            name='variant',
            unique_together=set([('reference', 'chrom', 'pos', 'ref', 'alt')]),
        ),
    ]
