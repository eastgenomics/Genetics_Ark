import django_tables2 as tables
from primer_db.models import PrimerDetails
from primer_db.models import Coordinates
from django.utils.html import format_html
from django_tables2 import A


# table used in index view for displaying all primers
  

class PrimerDetailsTable(tables.Table):
    name = tables.LinkColumn("edit_pair", args = [A('pk')])
    primer_id = tables.Column(accessor = "id")
    tm = tables.Column()
    status = tables.Column()
    snp_status = tables.Column(default = ' ', orderable=False)
    last_date_used = tables.Column()
    strand = tables.Column(accessor = "coordinates.strand")
    chrom_no = tables.Column(accessor = "coordinates.chrom_no")
    coverage37 = tables.Column(accessor = "pairs.coverage_37")
    coverage38 = tables.Column(accessor = "pairs.coverage_38")
    check = tables.CheckBoxColumn(verbose_name=" refewrf", accessor = 'pk')
    comments = tables.Column()


    def render_comments(comments, value):
        if len(value) > 100:
            return value[0:101] + "..."
        else:
            return value

    def render_tm(tm, value):
        # render tm to 2dp
        return '{:0.2f}'.format(value)

    def render_coverage37(coverage, value):
         return format_html('<a href="https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&lastVirtModeType=default&lastVirtModeExtraState=&virtModeType=default&virtMode=0&nonVirtPosition=&position={coverage}&hgsid=781179863_cVWc0XeuejyAZPhWCcXyCDrFkfDC"target="_blank">{coverage}</a>',
         coverage=value)
    
    def render_coverage38(coverage, value):
         return format_html('<a href="https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&lastVirtModeType=default&lastVirtModeExtraState=&virtModeType=default&virtMode=0&nonVirtPosition=&position={coverage}&hgsid=781192615_bQjbSysSF20VOBWn7VphryYc7GO8"target="_blank">{coverage}</a>',
         coverage=value)

    def render_status(status, value, column):
        # render status cell colour dependent on status

        if str(value) == "Archived":
            column.attrs = {'td': {'bgcolor': 'indianred'}}
        elif str(value) == "On Order":
            column.attrs = {'td': {'bgcolor': 'orange'}}
        else:
            column.attrs = {'td': {}}
        return value

    def render_snp_status(snp_status, value, column):
        # render SNP check cell colour dependent on presence of SNP check
        # 0 = not checked, 1 = no SNPs, 2 = SNPs detected, 3 = SNPs detected but manually checked

        if int(value) == 0:
            column.attrs = {'td': {'bgcolor': 'lemonchiffon'}}
            value = ''
        elif int(value) == 1:
            column.attrs = {'td': {'bgcolor': 'seagreen'}}
            value = ''
        elif int(value) == 2:
            column.attrs = {'td': {'bgcolor': 'indianred'}}
            value = ''
        elif int(value) == 3:
            column.attrs = {'td': {'bgcolor': 'lightskyblue'}}
            value = ''

        return value

    class Meta:	

        model = PrimerDetails
        attrs = {"class": "paleblue"}
        template_name = 'django_tables2/bootstrap.html'

        fields = ('primer_id', 'name', 'gene', 'sequence', 'gc_percent', 
                    'comments', 'arrival_date', 'status', 'tm', "strand",
                    'scientist', 'pcr_program', 'buffer', 'location', 
                    'snp_status', 'snp_date', 'snp_info', 'last_date_used')

        sequence = ('check', "primer_id", 'name', 'gene', 'sequence', 'gc_percent', 
                    'tm', 'chrom_no', 'coverage37', 'coverage38', "strand",
                    'buffer', 'pcr_program', 'scientist', 'arrival_date', 'location', 'last_date_used', 'status', 'snp_status', 'comments')

        exclude = ('reference','start37', 'end37','start38', 'end38', 'snp_date', 'snp_info')

        row_attrs = { 'data-status': lambda record: record.status}

        order_by = ("-primer_id", "name")