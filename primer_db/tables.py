import django_tables2 as tables
from primer_db.models import PrimerDetails
from primer_db.models import Coordinates
from django_tables2 import A

class PrimerDetailsTable(tables.Table):

	primer_name = tables.LinkColumn("edit_primer", args = [A('pk')])
	reference = tables.Column(accessor = "coordinates.reference")
	chrom_no = tables.Column(accessor = "coordinates.chrom_no")
	start = tables.Column(accessor="coordinates.start_coordinate_37")
	end = tables.Column(accessor = "coordinates.end_coordinate_37")

	class Meta:	

		model = PrimerDetails
		attrs = {"class": "paleblue"}
		template_name = 'django_tables2/bootstrap.html'

		fields = ('primer_name', 'sequence', 'gc_percent', 'tm', 
					'length', 'comments', 'arrival_date', 'status',
					'scientist', 'pcr_program', 'buffer')

		sequence = ('primer_name', 'sequence', 'gc_percent', 'length', 
					'tm', 'chrom_no', 'start', 'end', 'buffer', 
					'pcr_program', 'scientist', 'arrival_date', 'status', 'comments')

		exclude = ('reference',)

		


