import django_tables2 as tables
from primer_db.models import PrimerDetails
from primer_db.models import Coordinates
from django_tables2 import A


# table used in index view for displaying all primers

class PrimerDetailsTable(tables.Table):

	primer_name = tables.LinkColumn("edit_primer", args = [A('pk')])
	tm = tables.Column()
	reference = tables.Column(accessor = "coordinates.reference")
	chrom_no = tables.Column(accessor = "coordinates.chrom_no")
	coverage37 = tables.Column(accessor = "pairs.coverage_37")
	coverage38 = tables.Column(accessor = "pairs.coverage_38")
	check = tables.CheckBoxColumn(accessor = 'pk')
	# start37 = tables.Column(accessor="coordinates.start_coordinate_37")
	# end37 = tables.Column(accessor = "coordinates.end_coordinate_37")
	# start38 = tables.Column(accessor="coordinates.start_coordinate_38")
	# end38 = tables.Column(accessor = "coordinates.end_coordinate_38")
	
	def render_tm(tm, value):
		return '{:0.2f}'.format(value)

	class Meta:	

		model = PrimerDetails
		attrs = {"class": "paleblue"}
		template_name = 'django_tables2/bootstrap.html'

		#order_by = "-A('pk')"

		fields = ('primer_name', 'gene', 'sequence', 'gc_percent', 
					'comments', 'arrival_date', 'status', 'tm',
					'scientist', 'pcr_program', 'buffer', 'location')

		sequence = ('check', 'primer_name', 'gene', 'sequence', 'gc_percent', 
					'tm', 'chrom_no', 'buffer', 'coverage37', 'coverage38', 
					'pcr_program', 'scientist', 'arrival_date', 'location', 'status', 'comments')

		exclude = ('reference','start37', 'end37','start38', 'end38')

		


