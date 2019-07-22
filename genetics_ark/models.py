# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models
import genetics_ark.ccbg_misc as ccbg_misc


class Analysis(models.Model):
    sample               = models.ForeignKey('Sample', models.DO_NOTHING)
    runfolder            = models.ForeignKey('Runfolder', models.DO_NOTHING, blank=True, null=True)
    reference            = models.ForeignKey('Reference', models.DO_NOTHING, blank=True, null=True)
    status               = models.CharField(max_length=80, blank=True, null=True)
    total_reads          = models.IntegerField(blank=True, null=True)
    mapped_reads         = models.IntegerField(blank=True, null=True)
    duplicate_reads      = models.IntegerField(blank=True, null=True)
    mean_isize           = models.FloatField(blank=True, null=True)
    mean_het_ratio       = models.FloatField(blank=True, null=True)
    mean_homo_ratio      = models.FloatField(blank=True, null=True)
    gender               = models.CharField(max_length=1, blank=True, null=True)
    capture              = models.CharField(max_length=80, blank=True, null=True)
    bases_on_target      = models.FloatField(blank=True, null=True)
    mean_target_coverage = models.FloatField(blank=True, null=True)
    coverage_0x          = models.FloatField(blank=True, null=True)
    coverage_2x          = models.FloatField(blank=True, null=True)
    coverage_10x         = models.FloatField(blank=True, null=True)
    coverage_20x         = models.FloatField(blank=True, null=True)
    coverage_30x         = models.FloatField(blank=True, null=True)
    coverage_40x         = models.FloatField(blank=True, null=True)
    coverage_50x         = models.FloatField(blank=True, null=True)
    coverage_100x        = models.FloatField(blank=True, null=True)
    versions             = models.CharField(max_length=2000, blank=True, null=True)

    def __str__(self):
        return "{}\t{}\t{}".format(self.sample, self.runfolder, self.reference)

    class Meta:
        db_table = 'analysis'
        unique_together = (('sample', 'runfolder', 'reference'),)


class AnalysisVariant(models.Model):
    analysis     = models.ForeignKey(Analysis, models.DO_NOTHING)
    variant      = models.ForeignKey('Variant', models.DO_NOTHING)
    depth        = models.IntegerField(blank=True, null=True)
    aaf          = models.FloatField(db_column='AAF', blank=True, null=True)  # Field name made lowercase.
    quality      = models.FloatField(blank=True, null=True)
    gq           = models.FloatField(db_column='GQ', blank=True, null=True)  # Field name made lowercase.
    allele_count = models.IntegerField(blank=True, null=True)
    phase_key    = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return "{} <=> {}".format(self.analysis, self.variant)

    class Meta:
        db_table = 'analysis_variant'


class Annotation(models.Model):
    variant    = models.ForeignKey('Variant', models.DO_NOTHING)
    transcript = models.ForeignKey('Transcript', models.DO_NOTHING)
    effect     = models.CharField(max_length=80, blank=True, null=True)
    cpos       = models.CharField(max_length=80, blank=True, null=True)
    dna_change = models.CharField(db_column='DNA_change', max_length=80, blank=True, null=True)  # Field name made lowercase.
    aa_change  = models.CharField(db_column='AA_change', max_length=80, blank=True, null=True)  # Field name made lowercase.
    polyphen   = models.CharField(max_length=80, blank=True, null=True)
    sift       = models.CharField(max_length=80, blank=True, null=True)

    def __str__(self):
        return "{}\t{}".format(self.variant, self.transcript)

    class Meta:
        db_table = 'annotation'
        unique_together = (('variant', 'transcript'),)


class CNV(models.Model):
    chrom = models.CharField(max_length=2)
    start = models.PositiveIntegerField()
    end   = models.PositiveIntegerField()
    type  = models.CharField(max_length=15)


    def __str__(self):
        return "chrom{}: {}-{} {}".format(self.chrom, self.start, self.end, self.type)

    def get_samples(self):
        """ Function to get samples and their number for a given CNV

        - go to the DeconCNV to get decons
        - use the decon instances to get the samples
        """

        total_samples = []

        CNV2samples = DeconAnalysis.objects.filter(CNV_id__exact = self.id)

        for CNV2sample in CNV2samples:
            total_samples.append(CNV2sample.sample.name)

        total_samples = set(total_samples)

        return len(total_samples), total_samples

    class Meta:
        db_table = 'cnv'
        ordering = ['chrom', 'start', 'end', 'type']


class CNV_region(models.Model):
    CNV    = models.ForeignKey(CNV, on_delete=models.DO_NOTHING)
    region = models.ForeignKey("Region", on_delete=models.DO_NOTHING)

    def __str__(self):
        return "{} <=> {}".format(self.CNV, self.region)

    class Meta:
        db_table = "cnv_region"


class CNV_target(models.Model):
    ref          = models.ForeignKey("Reference", on_delete=models.DO_NOTHING)
    target_file  = models.CharField(max_length=50)

    def __str__(self):
        return self.target_file

    class Meta:
        db_table = 'cnv_target'
    

class Comment(models.Model):
    variant = models.ForeignKey("Variant", models.DO_NOTHING)
    user    = models.CharField(max_length = 80)
    date    = models.DateTimeField()
    comment = models.CharField(max_length = 200)

    def __str__(self):
        return "{}\t{}: {}".format(self.date, self.user, self.comment)

    class Meta:
        db_table = 'comment'
        ordering = ['date', 'user']


class Decon(models.Model):
    cnv_target = models.ForeignKey(CNV_target, on_delete=models.DO_NOTHING)
    runfolder  = models.ForeignKey('Runfolder', on_delete=models.DO_NOTHING)
    name       = models.CharField(max_length=100)
    date       = models.DateField('date of the run')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'decon'
        ordering = ['date', 'name']


class DeconAnalysis(models.Model):
    decon          = models.ForeignKey(Decon, on_delete=models.DO_NOTHING)
    CNV            = models.ForeignKey(CNV, on_delete=models.DO_NOTHING)
    sample         = models.ForeignKey('Sample', on_delete=models.DO_NOTHING)
    correlation    = models.FloatField()
    start_b        = models.PositiveIntegerField()
    end_b          = models.PositiveIntegerField()
    nb_exons       = models.PositiveIntegerField()
    BF             = models.FloatField()
    reads_expected = models.PositiveIntegerField()
    reads_observed = models.PositiveIntegerField()
    reads_ratio    = models.FloatField()

    def __str__(self):
        return "{} <=> {} <=> {}".format(self.decon, self.CNV, self.sample)

    class Meta:
        db_table = 'decon_analysis'
        indexes = [
            models.Index(fields=['decon',]),
            models.Index(fields=['CNV',]),
        ]
        ordering = ['CNV', 'sample']


class Gene(models.Model):
    name    = models.CharField(max_length=80, blank=True, null=True)
    hgnc    = models.IntegerField(blank=True, null=True)
    comment = models.CharField(max_length=800, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'gene'


class GenePanel(models.Model):
    panel = models.ForeignKey('Panel', models.DO_NOTHING)
    gene  = models.ForeignKey(Gene, models.DO_NOTHING)

    def __str__(self):
        return "{} <=> {}".format(self.panel, self.gene)

    class Meta:
        db_table = 'gene_panel'


class Meta(models.Model):
    meta_key     = models.CharField(max_length=40, blank=True, null=True)
    meta_value   = models.CharField(max_length=255, blank=True, null=True)
    meta_comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'meta'


class Model(models.Model):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'model'


class ModelRegion(models.Model):
    model  = models.ForeignKey(Model, models.DO_NOTHING)
    region = models.ForeignKey('Region', models.DO_NOTHING)

    def __str__(self):
        return "{} <=> {}".format(self.model, self. region)

    class Meta:
        db_table = 'model_region'


class Panel(models.Model):
    name   = models.CharField(max_length=200)
    ext_id = models.IntegerField(blank=True, null=True)
    active = models.CharField(max_length=1, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'panel'


class Project(models.Model):
    name   = models.CharField(unique=True, max_length=80)
    prefix = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'project'


class Reference(models.Model):
    name = models.CharField(unique=True, max_length=80)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'reference'


class Region(models.Model):
    reference = models.ForeignKey(Reference, models.DO_NOTHING)
    chrom     = models.CharField(max_length=80)
    start     = models.IntegerField()
    end       = models.IntegerField()

    def __str__(self):
        return "{}\t{}\t{}".format(self.chrom, self.start, self.end)

    class Meta:
        db_table = 'region'


class Runfolder(models.Model):
    name                = models.CharField(unique=True, max_length=80)
    samples             = models.IntegerField(blank=True, null=True)
    total_reads         = models.BigIntegerField(blank=True, null=True)
    mapped_reads        = models.BigIntegerField(blank=True, null=True)
    duplicate_reads     = models.BigIntegerField(blank=True, null=True)
    mean_isize          = models.FloatField(blank=True, null=True)
    bases_on_target     = models.FloatField(blank=True, null=True)
    bases_20x_coverage  = models.FloatField(blank=True, null=True)
    bases_100x_coverage = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'runfolder'

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
        analysis_count      = 0

        for analysis in ( Analysis.objects.filter( runfolder_id__exact = self.id )):
            

#            if ( not hasattr( analysis, 'stats')):
#                print "No stats for {}".format( analysis.name )
#                continue

            skip = 0

            from django.forms.models import model_to_dict
            
            if ( not ccbg_misc.is_a_number(analysis.total_reads)):
                skip += 1

            if (not ccbg_misc.is_a_number(analysis.mapped_reads)):
                skip += 1

            if (not ccbg_misc.is_a_number(analysis.duplicate_reads)):
                skip += 1

            if (not ccbg_misc.is_a_number(analysis.mean_isize)):
                skip += 1

            if (not ccbg_misc.is_a_number(analysis.bases_on_target)):
                skip += 1
        
            if (not ccbg_misc.is_a_number(analysis.coverage_100x)):
                skip += 1


            if ( skip ):
#                print "Skipping {}/{}".format( analysis.name, skip )
                continue
            
            total_reads         += analysis.total_reads
            mapped_reads        += analysis.mapped_reads
            duplicate_reads     += analysis.duplicate_reads
            mean_isize          += analysis.mean_isize
            bases_on_target     += analysis.bases_on_target
            bases_100x_coverage += analysis.coverage_100x
            analysis_count        += 1


        if ( analysis_count == 0 ):
#            print "No analysiss?"
            return self


        mean_isize          /= analysis_count
        bases_on_target     /= analysis_count
        bases_100x_coverage /= analysis_count
        
        self.analysis            = analysis_count
        self.total_reads         = total_reads
        self.mapped_reads        = mapped_reads
        self.duplicate_reads     = duplicate_reads
        self.mean_isize          = mean_isize
        self.bases_on_target     = bases_on_target
        self.bases_100x_coverage = bases_100x_coverage

        self.save()

        print(self.name)

#        pp.pprint( self )
        return self



class Sample(models.Model):
    project    = models.ForeignKey(Project, models.DO_NOTHING, blank=True, null=True)
    name       = models.CharField(unique=True, max_length=80)
    labid      = models.CharField(max_length=80, blank=True, null=True)
    first_name = models.CharField(max_length=80, blank=True, null=True)
    last_name  = models.CharField(max_length=80, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sample'


class SamplePanel(models.Model):
    sample     = models.ForeignKey(Sample, models.DO_NOTHING)
    panel_name = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return "{} <=> {}".format(self.sample, self.panel_name)

    class Meta:
        db_table = 'sample_panel'


class Transcript(models.Model):
    gene                = models.ForeignKey(Gene, models.DO_NOTHING)
    refseq              = models.CharField(max_length=200, blank=True, null=True)
    ens_id              = models.CharField(max_length=200, blank=True, null=True)
    ccds                = models.CharField(db_column='CCDS', max_length=200, blank=True, null=True)  # Field name made lowercase.
    clinical_transcript = models.CharField(max_length=1, blank=True, null=True)
    comment             = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.refseq

    class Meta:
        db_table = 'transcript'


class TranscriptRegion(models.Model):
    transcript = models.ForeignKey(Transcript, models.DO_NOTHING)
    region     = models.ForeignKey(Region, models.DO_NOTHING)
    exon_nr    = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return "{} <=> {}".format(self.transcript, self.region)

    class Meta:
        db_table = 'transcript_region'


class Variant(models.Model):
    reference = models.ForeignKey(Reference, models.DO_NOTHING)
    chrom     = models.CharField(max_length=8)
    pos       = models.IntegerField()
    ref       = models.CharField(max_length=100)
    alt       = models.CharField(max_length=100)

    def __str__(self):
        return "{}\t{}\t{}".format(self.chrom, self.pos, self.ref)

    class Meta:
        db_table = 'variant'
        unique_together = (('reference', 'chrom', 'pos', 'ref', 'alt'),)
