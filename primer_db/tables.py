import django_tables2 as tables
from primer_db.models import PrimerDetails
from primer_db.models import Coordinates
from django_tables2 import A


# table used in index view for displaying all primers

class PrimerDetailsTable(tables.Table):



	primer_name = tables.LinkColumn("edit_primer", args = [A('pk')])
	tm = tables.Column()
	status = tables.Column()
	reference = tables.Column(accessor = "coordinates.reference")
	chrom_no = tables.Column(accessor = "coordinates.chrom_no")
	coverage37 = tables.Column(accessor = "pairs.coverage_37")
	coverage38 = tables.Column(accessor = "pairs.coverage_38")
	check = tables.CheckBoxColumn(verbose_name=" refewrf", accessor = 'pk')
	# start37 = tables.Column(accessor="coordinates.start_coordinate_37")
	# end37 = tables.Column(accessor = "coordinates.end_coordinate_37")
	# start38 = tables.Column(accessor="coordinates.start_coordinate_38")
	# end38 = tables.Column(accessor = "coordinates.end_coordinate_38")
	
	def render_tm(tm, value):
		# render tm to 2dp
		return '{:0.2f}'.format(value)


	def render_status(status, value, column):
		# render status cell colour dependent on status

		if str(value) == "Archived":
			column.attrs = {'td': {'bgcolor': 'pink'}}
		elif str(value) == "On Order":
			column.attrs = {'td': {'bgcolor': 'orange'}}
		else:
			column.attrs = {'td': {}}
		return value


	class Meta:	

		model = PrimerDetails
		attrs = {"class": "paleblue"}
		template_name = 'django_tables2/bootstrap.html'

		#order_by = "arrival_date"

		fields = ('primer_name', 'gene', 'sequence', 'gc_percent', 
					'comments', 'arrival_date', 'status', 'tm',
					'scientist', 'pcr_program', 'buffer', 'location')

		sequence = ('check', 'primer_name', 'gene', 'sequence', 'gc_percent', 
					'tm', 'chrom_no', 'buffer', 'coverage37', 'coverage38', 
					'pcr_program', 'scientist', 'arrival_date', 'location', 'status', 'comments')

		exclude = ('reference','start37', 'end37','start38', 'end38')

		row_attrs = { 'data-status': lambda record: record.status}


