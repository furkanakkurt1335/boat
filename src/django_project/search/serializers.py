from django.contrib.auth.models import User, Group
from rest_framework import serializers
from app1.models import Sentence, Annotation, Word_Line
from django_filters import rest_framework as filters

class SentenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sentence
        fields = ['url', 'order', 'treebank', 'sent_id', 'text', 'comments']
    
class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = ['url', 'annotator', 'sentence', 'notes']

class WordLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word_Line
        fields = ['url', 'form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc']

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']