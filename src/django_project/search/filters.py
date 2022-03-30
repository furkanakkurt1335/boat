from app1.models import Word_Line, Annotation
from django_filters import rest_framework as filters

class WordLineFilter(filters.FilterSet):
    class Meta:
        model = Word_Line
        # fields = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc', 'sentence__sent_id', 'sentence__text']
        fields = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc', 'id']

class AnnotationFilter(filters.FilterSet):
    class Meta:
        model = Annotation
        # fields = ['sentence__sent_id', 'sentence__text']
        fields = []