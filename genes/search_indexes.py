import datetime
from haystack import indexes
from genes.models import Gene
from django.db.models import Max, Min

cache_weights = {}#had to cache this, without the cache rebuilding the index crushed postgres

class GeneIndex(indexes.SearchIndex, indexes.Indexable):
    text        = indexes.CharField(document=True, use_template=True)
    organism    = indexes.CharField(model_attr="organism__slug")
    obsolete    = indexes.BooleanField(model_attr="obsolete")
    std_name    = indexes.CharField(model_attr="standard_name")

    def prepare(self, obj):
        data = super(GeneIndex, self).prepare(obj)
        try: #had to cache these, w/o rebuilding index used too much CPU on the aggregate calls
            (min_weight, max_weight) = cache_weights[obj.organism.slug]
        except KeyError:
            min_weight = Gene.objects.filter(organism=obj.organism).aggregate(Min('weight'))['weight__min']
            max_weight = Gene.objects.filter(organism=obj.organism).aggregate(Max('weight'))['weight__max']
            cache_weights[obj.organism.slug] = (min_weight, max_weight)
        #boost by at most 10% for genes that are widely referred to
        #this helps to solve the duplicate mapping problem
        #see https://django-haystack.readthedocs.org/en/latest/boost.html
        #as well as code in the loading of gene_info files to estimate a weight
        try:
            data['boost'] = 0.1 * (obj.weight - min_weight)/(max_weight - min_weight) + 1
        except ZeroDivisionError: #on the first load, the max and min weights are zero
            data['boost'] = 1
        return data

    def get_model(self):
        return Gene

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


