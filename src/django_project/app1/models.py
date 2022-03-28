from django.db import models
from django.contrib.auth.models import User
from spacy import blank

class ExtendUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    preferences = models.JSONField(blank=True)

class TreebankManager(models.Manager):
    def get_treebank_from_url(self, url):
        treebanks = Treebank.objects.all()
        for treebank_t in treebanks:
            if treebank_t.title.replace(' ', '-') == url: return treebank_t
        return None

class Treebank(models.Model):
    title = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.title

    objects = TreebankManager()

class SentenceManager(models.Manager):
    def create_sentence(self, treebank, sent_id, text, comments={}):
        if len(Sentence.objects.filter(treebank=treebank)) == 0: next_order = 1
        else: next_order = list(Sentence.objects.filter(treebank=treebank).order_by('order'))[-1].order + 1
        sentence = self.create(order=next_order, treebank=treebank, sent_id=sent_id, text=text, comments=comments)
        return sentence

class Sentence(models.Model):
    class Meta:
        unique_together = ['sent_id', 'text']

    order = models.PositiveIntegerField()
    treebank = models.ForeignKey(Treebank, on_delete=models.CASCADE)
    sent_id = models.CharField(max_length=30)
    text = models.TextField()
    comments = models.JSONField(blank=True)

    objects = SentenceManager()

    def __str__(self):
        return self.sent_id

class AnnotationManager(models.Manager):
    def create_annotation(self, annotator, sentence, notes=''):
        annotation = self.create(annotator=annotator, sentence=sentence, notes=notes)
        return annotation

class Annotation(models.Model):
    annotator = models.ForeignKey(User, on_delete=models.CASCADE)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    notes = models.TextField()

    objects = AnnotationManager()

    def __str__(self):
        return '%s by %s' % (self.sentence.sent_id, self.annotator)

class Word_LineManager(models.Manager):
    def create_word_line(self, annotation, id_f, form_f, lemma, upos, xpos, feats, head, deprel, deps, misc):
        word_line = self.create(annotation=annotation, id_f=id_f, form_f=form_f, lemma=lemma, upos=upos, xpos=xpos, feats=feats, head=head, deprel=deprel, deps=deps, misc=misc)
        return word_line

class Word_Line(models.Model):
    annotation = models.ForeignKey(Annotation, on_delete=models.CASCADE)
    id_f = models.CharField(max_length=10)
    form_f = models.CharField(max_length=100)
    lemma = models.CharField(max_length=100)
    upos = models.CharField(max_length=100)
    xpos = models.CharField(max_length=100)
    feats = models.CharField(max_length=500)
    head = models.CharField(max_length=100)
    deprel = models.CharField(max_length=100)
    deps = models.CharField(max_length=100)
    misc = models.CharField(max_length=200)

    objects = Word_LineManager()

    def __str__(self):
        return '%s, ID: %s' % (self.annotation, self.id_f)
