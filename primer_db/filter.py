import django_filters
import primer_db.models as Models

class PrimerNameFilter(django_filters.FilterSet):
	#primer_name = django_filters.CharFilter(lookup_expr='icontains')

	class Meta:
		model = Models.PrimerDetails
		fields = ['primer_name',]