from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import UserSerializer, GroupSerializer, TreebankSerializer, SentenceSerializer, AnnotationSerializer, WordLineSerializer
from app1.models import Treebank, Sentence, Annotation, Word_Line
from django_filters import rest_framework as filters
from django_filters import CharFilter

class WordLineViewSet(viewsets.ModelViewSet):
    class WordLineFilter(filters.FilterSet):
        id = CharFilter(lookup_expr='iexact')
        annotation__id = CharFilter(lookup_expr='iexact')
        class Meta:
            model = Word_Line
            fields = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc', 'id', 'annotation__id', 'annotation__sentence__sent_id', 'annotation__sentence__text', 'annotation__sentence__treebank__title']
    queryset = Word_Line.objects.all()
    serializer_class = WordLineSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend,]
    filterset_class = WordLineFilter

class AnnotationViewSet(viewsets.ModelViewSet):
    class AnnotationFilter(filters.FilterSet):
        id = CharFilter(lookup_expr='iexact')
        class Meta:
            model = Annotation
            fields = ['annotator__id', 'sentence__sent_id', 'sentence__text', 'status']
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend,]
    filterset_class = AnnotationFilter

class SentenceViewSet(viewsets.ModelViewSet):
    class SentenceFilter(filters.FilterSet):
        id = CharFilter(lookup_expr='iexact')
        class Meta:
            model = Sentence
            fields = ['treebank__title', 'sent_id', 'text']
    queryset = Sentence.objects.all()
    serializer_class = SentenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend,]
    filterset_class = SentenceFilter

class TreebankViewSet(viewsets.ModelViewSet):
    class TreebankFilter(filters.FilterSet):
        id = CharFilter(lookup_expr='iexact')
        class Meta:
            model = Treebank
            fields = ['title']
    queryset = Treebank.objects.all()
    serializer_class = TreebankSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend,]
    filterset_class = TreebankFilter

class UserViewSet(viewsets.ModelViewSet):
    class UserFilter(filters.FilterSet):
        id = CharFilter(lookup_expr='iexact')
        class Meta:
            model = User
            fields = ['username']
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend,]
    filterset_class = UserFilter

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]