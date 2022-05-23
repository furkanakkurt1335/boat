from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import UserSerializer, GroupSerializer, TreebankSerializer, SentenceSerializer, AnnotationSerializer, WordLineSerializer
from ui.models import Treebank, Sentence, Annotation, Word_Line
from django_filters import rest_framework as filters
from django_filters import CharFilter

from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view()
def get_treebank(request):
    q = request.GET
    treebank_title = q['treebank_title']
    sentences = Sentence.objects.filter(treebank__title=treebank_title)
    result = {}
    for sentence in sentences:
        result[len(result.keys())] = {'sent_id': sentence.sent_id, 'text': sentence.text, 'order': sentence.order}
    return Response(result)

@api_view()
def my_annotations(request):
    q = request.GET
    if 'type' not in q:
        return Response({"error": "Type should be given."})
    if q['type'] == 'all':
        annotations = Annotation.objects.filter(annotator=request.user)
    else:
        type_d = {"not": 0, "half": 2, "done": 1}
        annotations = Annotation.objects.filter(annotator=request.user, status=type_d[q['type']])
    result = {}
    for ann_t in annotations:
        sen_t = Sentence.objects.get(id=ann_t.sentence.id)
        tb_t = Treebank.objects.get(id=sen_t.treebank_id)
        d_t = {'sent_id': sen_t.sent_id, 'text': sen_t.text, 'treebank_title': tb_t.title}
        result[len(result.keys())] = d_t
    return Response(result)

@api_view()
def query(request):
    q = request.GET
    wordlines = Word_Line.objects.all()
    if 'form' in q:
        wordlines = wordlines.filter(form__contains=q['form'])
    if 'lemma' in q:
        wordlines = wordlines.filter(lemma__contains=q['lemma'])
    if 'upos' in q:
        wordlines = wordlines.filter(upos__contains=q['upos'])
    if 'xpos' in q:
        wordlines = wordlines.filter(xpos__contains=q['xpos'])
    if 'feats' in q:
        wordlines = wordlines.filter(feats__contains=q['feats'])
    if 'head' in q:
        wordlines = wordlines.filter(head__contains=q['head'])
    if 'deprel' in q:
        wordlines = wordlines.filter(deprel__contains=q['deprel'])
    if 'deps' in q:
        wordlines = wordlines.filter(deps__contains=q['deps'])
    if 'misc' in q:
        wordlines = wordlines.filter(misc__contains=q['misc'])
    if 'sent_id' in q:
        wordlines = wordlines.filter(annotation__sentence__sent_id__contains=q['sent_id'])
    if 'text' in q:
        wordlines = wordlines.filter(annotation__sentence__text__icontains=q['text'])
    if 'treebank_title' in q:
        wordlines = wordlines.filter(annotation__sentence__treebank__title__contains=q['treebank_title'])
    result = {}
    for wl_t in wordlines:
        if wl_t.annotation_id in result.keys(): continue
        ann_t = Annotation.objects.get(id=wl_t.annotation_id)
        sen_t = Sentence.objects.get(id=ann_t.sentence_id)
        user_t = User.objects.get(id=ann_t.annotator_id)
        tb_t = Treebank.objects.get(id=sen_t.treebank_id)
        wls = Word_Line.objects.filter(annotation=ann_t)
        wls_d = {}
        for wl in wls:
            wls_d[wl.id_f] = {'form': wl.form, 'lemma': wl.lemma, 'upos': wl.upos, 'xpos': wl.xpos, 'feats': wl.feats, 'head': wl.head, 'deprel': wl.deprel, 'deps': wl.deps, 'misc': wl.misc}
        d_t = {'text': sen_t.text, 'sent_id': sen_t.sent_id, 'annotator': user_t.username, 'status': ann_t.status, 'treebank_title': tb_t.title, 'order': sen_t.order, 'wordlines': wls_d}
        result[wl_t.annotation_id] = d_t
    return Response(result)

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
        sentence__order = CharFilter(lookup_expr='iexact')
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
            fields = ['username', 'first_name', 'last_name']
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