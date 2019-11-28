import django_tables2 as tables
from primer_db.models import PrimerDetails
from primer_db.models import Coordinates
from django_tables2 import A


# table used in index view for displaying all primers

class PrimerDetailsTable(tables.Table):
	name = tables.LinkColumn("edit_pair", args = [A('pk')])
	tm = tables.Column()
	status = tables.Column()
	snp_status = tables.Column(default = ' ')
	reference = tables.Column(accessor = "coordinates.reference")
	chrom_no = tables.Column(accessor = "coordinates.chrom_no")
	coverage37 = tables.Column(accessor = "pairs.coverage_37")
	coverage38 = tables.Column(accessor = "pairs.coverage_38")
	check = tables.CheckBoxColumn(verbose_name=" refewrf", accessor = 'pk')
	# start37 = tables.Column(accessor="coordinates.start_coordinate_37")
	# end37 = tables.Column(accessor = "coordinates.end_coordinate_37")
	# start38 = tables.Column(accessor="coordinates.start_coordinate_38")
	# end38 = tables.Column(accessor = "coordinates.end_coordinate_38")
	
	def render_tm(self.tm, value):
		# render tm to 2dp
		return '{:0.2f}'.format(value)

	def render_status(self.status, value, column):
		# render status cell colour dependent on status

		if str(value) == "Archived":
			column.attrs = {'td': {'bgcolor': 'indianred'}}
		elif str(value) == "On Order":
			column.attrs = {'td': {'bgcolor': 'orange'}}
		else:
			column.attrs = {'td': {}}
		return value

	def render_snp_status(self.snp_status, value, column):
		# render SNP check cell colour dependent on presence of SNP check
		# 0 = not checked, 1 = no SNPs, 2 = SNPs detected

		if int(value) == 0:
			column.attrs = {'td': {'bgcolor': 'lemonchiffon'}}
			value = ''
		elif int(value) == 1:
			column.attrs = {'td': {'bgcolor': 'seagreen'}}
			value = ''
		elif int(value) == 2:
			column.attrs = {'td': {'bgcolor': 'indianred'}}
			value = ''

		return value

	class Meta:	

		model = PrimerDetails
		attrs = {"class": "paleblue"}
		template_name = 'django_tables2/bootstrap.html'

		fields = ('name', 'gene', 'sequence', 'gc_percent', 
					'comments', 'arrival_date', 'status', 'tm',
					'scientist', 'pcr_program', 'buffer', 'location', 
					'snp_status', 'snp_date', 'snp_info')

		sequence = ('check', 'name', 'gene', 'sequence', 'gc_percent', 
					'tm', 'chrom_no', 'buffer', 'coverage37', 'coverage38', 
					'pcr_program', 'scientist', 'arrival_date', 'location', 'status', 'snp_status', 'comments')

		exclude = ('reference','start37', 'end37','start38', 'end38', 'snp_date', 'snp_info')

		row_attrs = { 'data-status': lambda record: record.status}
