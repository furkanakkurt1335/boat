from django.contrib.auth.models import User, Group
from rest_framework import serializers
from app1.models import *

class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word_Line
        fields = ['url', 'form_f', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps']

class SentenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sentence
        fields = ['url', 'order', 'treebank', 'sent_id', 'text', 'comments']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']