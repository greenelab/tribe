from haystack import indexes
from django.db.models import Max, Min
from genes.models import Gene

# Had to cache this. Without the cache, rebuilding the index would crush
# the database.
cache_weights = {}


class GeneIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    organism = indexes.CharField(model_attr="organism__slug")
    obsolete = indexes.BooleanField(model_attr="obsolete")
    std_name = indexes.CharField(model_attr="standard_name")

    def prepare(self, obj):
        data = super(GeneIndex, self).prepare(obj)
        # Had to cache these, otherwise too much CPU would be used on
        # aggregate calls.
        try:
            (min_weight, max_weight) = cache_weights[obj.organism.slug]
        except KeyError:
            min_weight = Gene.objects.filter(organism=obj.organism).aggregate(
                Min('weight'))['weight__min']
            max_weight = Gene.objects.filter(organism=obj.organism).aggregate(
                Max('weight'))['weight__max']
            cache_weights[obj.organism.slug] = (min_weight, max_weight)

        # Boost by at most 10% for genes that are widely referred to.  This
        # helps to solve the duplicate mapping problem. See:
        # https://django-haystack.readthedocs.org/en/latest/boost.html
        # as well as management/commands/genes_load_geneinfo.py to estimate a
        # weight.
        try:
            data['boost'] = 0.1 * (obj.weight - min_weight) / (
                max_weight - min_weight) + 1
        # On the first load, the max and min weights are zero.
        except ZeroDivisionError:
            data['boost'] = 1

        return data

    def get_model(self):
        return Gene

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
