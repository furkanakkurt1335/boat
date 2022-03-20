from django.contrib import admin
from .models import Treebank, Sentence, Annotation

admin.site.register(Treebank)
admin.site.register(Sentence)
admin.site.register(Annotation)