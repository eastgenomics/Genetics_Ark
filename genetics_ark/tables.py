import django_tables2 as tables

from django_tables2.utils import A 
from django.core.urlresolvers import reverse
import django.utils.safestring


class SampleAAFTable(tables.Table):

    name            = tables.LinkColumn('sample_view', args=[A('name')], verbose_name='Sample')
    depth           = tables.Column(verbose_name="Depth")
    quality         = tables.Column(verbose_name="Quality")
    aaf             = tables.Column(verbose_name="AAF")
    allele_count    = tables.Column(verbose_name="Genotype")
#    panels          = tables.LinkColumn('panels', args=[A('panel_name')], verbose_name='Panel(s)')
    panels          = tables.Column(verbose_name="Panels")

    class Meta:
        attrs = {"class": "paleblue"}


    def render_allele_count(self, value):
        if value == 2:
            return "Hom"
        elif value == 1:
            return "Het"
        else:
            return "Unk"


class VariantFreqTable(tables.Table):

    vid      = tables.Column(verbose_name="VID")
    position = tables.LinkColumn('freq_view', args=[A('chr'), A('pos')], verbose_name='Position')
#    position = tables.Column(verbose_name="Variant")
    project  = tables.Column(verbose_name="Project")
    freq     = tables.Column(verbose_name="Frequency")
    hets     = tables.Column(verbose_name="Nr of Hets")
    homs     = tables.Column(verbose_name="Nr of Homs")
    effect   = tables.Column(verbose_name="Effect")

    class Meta:
        attrs = {"class": "paleblue"}



class SampleReportTable(tables.Table):
    
#    rpid               = tables.LinkColumn('vars_report', args=[A('rpid')], verbose_name='Report')
#    filename           = tables.Column(verbose_name="Filename")
    view               = tables.Column(verbose_name="")
    def render_view(self, value ):
        button = "<a href='%s' type='button' class='btn btn-secondary'>View</a>" % value
        return django.utils.safestring.mark_safe( button )

    edit               = tables.Column(verbose_name="")
    def render_edit(self, value ):
        button = "<a href='%s' type= 'button' class= 'btn btn-secondary'>Edit</a>" % value
        return django.utils.safestring.mark_safe( button )

    status             = tables.Column(verbose_name="Status")

    def render_status(self, value ):
        button = "<a  type= 'button' class= 'btn btn-secondary' disabled>%s</a>" % value
        return django.utils.safestring.mark_safe( button )

#    rpid               = tables.LinkColumn('report_view', args=[A('rpid')], verbose_name='Report')
    created            = tables.Column(verbose_name="Created")
    panels             = tables.Column(verbose_name="Panel(s)")

#    avg_coverage       = tables.Column(verbose_name="Avg Coverage")
#    stop_gained        = tables.Column(verbose_name="Stop gained")
#    frameshift_variant = tables.Column(verbose_name="Frameshift(s)")
#    consensus_splice   = tables.Column(verbose_name="Splicesite")
#    missense_variant   = tables.Column(verbose_name="Misesnse")
#    synonymous         = tables.Column(verbose_name="Sense")

    class Meta:
        attrs = {"class": "paleblue"}

class SampleVariantTable(tables.Table):


    vid        = tables.Column(verbose_name="VID")
    position   = tables.LinkColumn('freq_view', args=[A('chr'), A('pos')], verbose_name='Position')

    gene       = tables.Column(verbose_name="Gene")
#    effect     = tables.Column(verbose_name="Effect")
    transcript = tables.Column(verbose_name="Transcript")
    cpos       = tables.Column(verbose_name="cpos")
    dna_change = tables.Column(verbose_name="DNA change")
    aa_change  = tables.Column(verbose_name="AA change")
    score      = tables.Column(verbose_name="Score")
    depth      = tables.Column(verbose_name="Depth")
    aaf        = tables.Column(verbose_name="AAF")
    genotype   = tables.Column(verbose_name="Genotype")
#    dbsnp      = tables.Column(verbose_name="dbSNP")
    polyphen   = tables.Column(verbose_name="PolyPhen")
    sift       = tables.Column(verbose_name="Sift")

    af_gemini  = tables.Column(verbose_name="Gemini")
#    af_1kg     = tables.Column(verbose_name="1KG")
#    af_exac    = tables.Column(verbose_name="Exact")
#    af_esp     = tables.Column(verbose_name="ESP")



    class Meta:
        attrs = {"class": "paleblue"}

    


class GeneTable(tables.Table):

#    name            = tables.LinkColumn('qc_runfolder_stats', args=[A('rfid')], verbose_name='Name')
    name                = tables.Column(verbose_name="Gene")
    refseq              = tables.Column(verbose_name="RefSeq")
    ens_id              = tables.Column(verbose_name="ENSID")
    clinical_transcript = tables.Column(verbose_name="Clinical Transcript")

    class Meta:
        attrs = {"class": "paleblue"}

    def render_clinical_transcript(self, value):
         if ( value == 'Y'):
             return "Yes"
         else:
             return "No"


class ProjectTable(tables.Table):

    name            = tables.LinkColumn('qc_project', args=[A('id')], verbose_name='Name')
#    name                = tables.Column(verbose_name="Name")
    samples             = tables.Column(verbose_name="Samples")

    class Meta:
        attrs = {"class": "paleblue"}




class CoverageTable(tables.Table):


    exon_nr         = tables.Column(verbose_name="Exon nr")
    length          = tables.Column(verbose_name="Length")
    min             = tables.Column(verbose_name="Min Coverage")
    mean            = tables.Column(verbose_name="Mean Coverage")
    max             = tables.Column(verbose_name="Max Coverage")
    exp_mean        = tables.Column(verbose_name="Expected mean")

    missing         = tables.Column(verbose_name="0x")
    coverage_1to5   = tables.Column(verbose_name="1-5x")
    coverage_6to9   = tables.Column(verbose_name="6-9x")
    coverage_10to19 = tables.Column(verbose_name="10-19x")
    coverage_20x    = tables.Column(verbose_name=">20x")

#    def render_exp_mean(self, value):
#        return "%.2f" % value.mean 


    class Meta:
        attrs = {"class": "paleblue"}

        
class StatsTable(tables.Table):

#    name            = tables.Column(verbose_name="Name", order_by='name')
    name            = tables.LinkColumn('qc_runfolder', args=[A('id')], verbose_name='Name')
    total_reads     = tables.Column(verbose_name="Total reads")
    perc_mapped     = tables.Column(verbose_name="% mapped reads")
    perc_dups       = tables.Column(verbose_name="% duplicate reads")
    bases_on_target = tables.Column(verbose_name="% bases on target")
#    bases_on_target_boxplot =  tables.Column( verbose_name="On target Performance" )
    mean_isize      = tables.Column(verbose_name="Mean isize")
#    project         = tables.Column(verbose_name="Project")
#    project         = tables.TemplateColumn( "", verbose_name="Project" )
#    project         = tables.Column( verbose_name='Project' )
#    mean_coverage   = tables.Column(verbose_name="Mean coverage")
    coverage_100x   = tables.Column(verbose_name="% bases > 100x coverage")

    class Meta:
        attrs = {"class": "paleblue"}

#    def render_total_reads(self, value):
#        return readable_number(value)

#    def render_perc_mapped(self, value):
#        return "%.2f%%" % value 

#    def render_perc_dups(self, value):
#        return '%.2f %%' % (value)

#    def render_bases_on_target(self, value):
#        return '%.2f %%' % (value*100.0)

#    def render_mean_isize(self, value):
#        return readable_number( value )


class SampleTable(tables.Table):

#    name            = tables.Column(verbose_name='Name')
#    name            = tables.Column(verbose_name='Name')
    name            = tables.LinkColumn('sample_view', args=[A('name')], verbose_name='Name')
    total_reads     = tables.Column(verbose_name="Total reads")
    perc_mapped     = tables.Column(verbose_name="% mapped reads")
    perc_dups       = tables.Column(verbose_name="% duplicate reads")
    bases_on_target = tables.Column(verbose_name="% bases on target")
#    bases_on_target_boxplot =  tables.Column( verbose_name="On target Performance" )
    mean_isize      = tables.Column(verbose_name="Mean isize")
    coverage_20x   = tables.Column(verbose_name="% bases > 100x coverage")
    coverage_100x   = tables.Column(verbose_name="% bases > 100x coverage")
#    edit            = tables.Column(verbose_name="Edit")

    class Meta:
        attrs = {"class": "paleblue"}

    def render_total_reads(self, value):
        return readable_number(value)

    def render_perc_mapped(self, value):
        return "%.2f%%" % value 

    def render_perc_dups(self, value):
        return '%.2f %%' % (value)

    def render_bases_on_target(self, value):
        return '%.2f %%' % (value)

    def render_mean_isize(self, value):
        return readable_number( value )

    def render_edit(self):
        return "<a href='http://www.theonion.com'> EDIT </a>"



def readable_number( value ):    

    if ( type( value ) is not int and type( value ) is not float):
        return value

    if (value > 1000000000):
        value = "%.2fB" %( value*1.0/ 1000000000)
    elif (value > 1000000):
        value = "%.2fM" %( value*1.0/ 1000000)
    elif (value > 1000):
        value = "%.2fK" %( value*1.0/ 1000)
    elif ( type( value ) is float ):
        value = "%.2f" % value

    return value
