from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import UserSerializer, GroupSerializer, SentenceSerializer, AnnotationSerializer, WordLineSerializer
from app1.models import Sentence, Annotation, Word_Line
from rest_framework import filters
from django_filters import rest_framework as d_filters

class WordLineViewSet(viewsets.ModelViewSet):
    class WordLineFilter(d_filters.FilterSet):
        class Meta:
            model = Word_Line
            fields = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc', 'annotation__sentence__sent_id', 'annotation__sentence__text']
    queryset = Word_Line.objects.all()
    serializer_class = WordLineSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [d_filters.DjangoFilterBackend,]
    filterset_class = WordLineFilter

class AnnotationViewSet(viewsets.ModelViewSet):
    class AnnotationFilter(d_filters.FilterSet):
        class Meta:
            model = Annotation
            fields = ['sentence__sent_id', 'sentence__text']
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [d_filters.DjangoFilterBackend,]
    filterset_class = AnnotationFilter

class SentenceViewSet(viewsets.ModelViewSet):
    queryset = Sentence.objects.all()
    serializer_class = SentenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['treebank__title']

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]