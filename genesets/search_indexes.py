import re

from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes
from genesets.models import Geneset

NONWORD = re.compile('\W+')


class GenesetIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    class Meta:
        model = Geneset

    def prepare(self, object):
        self.prepared_data = super(GenesetIndex, self).prepare(object)

        # Make a txt field that contains the title and abstract split
        # by non-words.
        # This makes indexing things like "GO-BP-<ID#>:<GO title>"" easier.
        txts = NONWORD.split(object.title)

        # Add some logic in case the geneset has no abstract
        # otherwise haystack breaks when trying to index it:
        if object.abstract:
            txts.extend(NONWORD.split(object.abstract))
        self.prepared_data['text'] = self.prepared_data['text'] + ' ' + \
            ' '.join(txts)
        return self.prepared_data

    def get_model(self):
        return Geneset
