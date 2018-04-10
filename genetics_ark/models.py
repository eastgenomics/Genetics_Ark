# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models
import genetics_ark.ccbg_misc as ccbg_misc


class Project(models.Model):
    name = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'project'


class Runfolder(models.Model):
    name                = models.CharField(unique=True, max_length=80)
    samples             = models.IntegerField(blank=True, null=True)
    total_reads         = models.IntegerField(blank=True, null=True)
    mapped_reads        = models.IntegerField(blank=True, null=True)
    duplicate_reads     = models.IntegerField(blank=True, null=True)
    mean_isize          = models.FloatField(blank=True, null=True)
    bases_on_target     = models.FloatField(blank=True, null=True)
    bases_100x_coverage = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'runfolder'

    def __unicode(self):
        return self.name

    def perc_dups( self ):
        return duplicate_reads*100.0/total_reads

    #
    # Calculates the runfolder stats and stores them 
    #
    def calc_stats(self ):

#        print "Calculating stats for runfolder: {}".format(self.name)
        
        total_reads         = 0
        mapped_reads        = 0
        duplicate_reads     = 0
        mean_isize          = 0.0
        bases_on_target     = 0.0
        bases_100x_coverage = 0.0
        sample_count        = 0

        for sample in ( Sample.objects.filter( runfolder_id__exact = self.id )):
            

            if ( not hasattr( sample, 'stats')):
                print "No stats for {}".format( sample.name )
                continue

            skip = 0

            from django.forms.models import model_to_dict
            
            if ( not ccbg_misc.is_a_number(sample.stats.total_reads)):
                skip += 1

            if (not ccbg_misc.is_a_number(sample.stats.mapped_reads)):
                skip += 1

            if (not ccbg_misc.is_a_number(sample.stats.duplicate_reads)):
                skip += 1

            if (not ccbg_misc.is_a_number(sample.stats.mean_isize)):
                skip += 1

            if (not ccbg_misc.is_a_number(sample.stats.bases_on_target)):
                skip += 1
        
            if (not ccbg_misc.is_a_number(sample.stats.coverage_100x)):
                skip += 1


            if ( skip ):
                print "Skipping {}/{}".format( sample.name, skip )
                continue
            
            total_reads         += sample.stats.total_reads
            mapped_reads        += sample.stats.mapped_reads
            duplicate_reads     += sample.stats.duplicate_reads
            mean_isize          += sample.stats.mean_isize
            bases_on_target     += sample.stats.bases_on_target
            bases_100x_coverage += sample.stats.coverage_100x
            sample_count        += 1


        if ( sample_count == 0 ):
#            print "No samples?"
            return self


        mean_isize          /= sample_count
        bases_on_target     /= sample_count
        bases_100x_coverage /= sample_count
        
        self.sample              = sample_count
        self.total_reads         = total_reads
        self.mapped_reads        = mapped_reads
        self.duplicate_reads     = duplicate_reads
        self.mean_isize          = mean_isize
        self.bases_on_target     = bases_on_target
        self.bases_100x_coverage = bases_100x_coverage

        self.save()

        print self.name

#        pp.pprint( self )
        return self


        
class Sample(models.Model):
    name = models.CharField(max_length=80)
    status = models.CharField(max_length=80, blank=True, null=True)
    project = models.ForeignKey(Project, models.DO_NOTHING, blank=True, null=True)
    runfolder = models.ForeignKey(Runfolder, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample'
        unique_together = (('name', 'runfolder'),)


class SampleVariant(models.Model):
    sample = models.ForeignKey(Sample, models.DO_NOTHING)
    variant = models.ForeignKey('Variant', models.DO_NOTHING)
    depth = models.IntegerField(blank=True, null=True)
    aaf = models.FloatField(db_column='AAF', blank=True, null=True)  # Field name made lowercase.
    quality = models.FloatField(blank=True, null=True)
    gq = models.FloatField(db_column='GQ', blank=True, null=True)  # Field name made lowercase.
    allele_count = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sample_variant'


class Stats(models.Model):
    sample      = models.OneToOneField(Sample, primary_key=True, db_column='sample_id')
    total_reads = models.IntegerField(blank=True, null=True)
    mapped_reads = models.IntegerField(blank=True, null=True)
    duplicate_reads = models.IntegerField(blank=True, null=True)
    mean_isize = models.FloatField(blank=True, null=True)
    mean_het_ratio = models.FloatField(blank=True, null=True)
    mean_homo_ratio = models.FloatField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    capture = models.CharField(max_length=80, blank=True, null=True)
    bases_on_target = models.FloatField(blank=True, null=True)
    mean_target_coverage = models.FloatField(blank=True, null=True)
    coverage_0x = models.FloatField(db_column='0x_coverage', blank=True, null=True)
    coverage_2x = models.FloatField(db_column='2x_coverage', blank=True, null=True)
    coverage_10x = models.FloatField(db_column='10x_coverage', blank=True, null=True)
    coverage_20x = models.FloatField(db_column='20x_coverage', blank=True, null=True)
    coverage_30x = models.FloatField(db_column='30x_coverage', blank=True, null=True)
    coverage_40x = models.FloatField(db_column='40x_coverage', blank=True, null=True)
    coverage_50x = models.FloatField(db_column='50x_coverage', blank=True, null=True)
    coverage_100x = models.FloatField(db_column='100x_coverage', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stats'


class Variant(models.Model):
    chrom = models.CharField(max_length=8)
    pos = models.IntegerField()
    ref = models.CharField(max_length=100)
    alt = models.CharField(max_length=100)
    comment = models.CharField(max_length=200, blank=True, null=True)
    annotation_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'variant'
        unique_together = (('chrom', 'pos', 'ref', 'alt'),)


class Panel(models.Model):
    name = models.CharField(max_length=200)
    active = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'panel'


class SamplePanel(models.Model):
    sample      = models.OneToOneField(Sample, primary_key=True, db_column='sample_id')
    panel_name  =  models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample_panel'




class GenePanel(models.Model):
    panel = models.ForeignKey('Panel', models.DO_NOTHING)
    gene = models.ForeignKey('Gene', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'gene_panel'

class Gene(models.Model):
    name = models.CharField(max_length=80, blank=True, null=True)
    refseq = models.CharField(max_length=200, blank=True, null=True)
    ens_id = models.CharField(max_length=200, blank=True, null=True)
    ccds = models.CharField(db_column='CCDS', max_length=200, blank=True, null=True)  # Field name made lowercase.
    clinical_transcript = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gene'
