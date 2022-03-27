import django_filters
from app1.models import Word_Line
from django_filters import rest_framework as filters

class AnnotationFilter(filters.FilterSet):
    class Meta:
        model = Word_Line
        fields = ['form_f', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps']
