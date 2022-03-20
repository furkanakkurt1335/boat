from django.db import models
from django.contrib.auth.models import User

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
        sentence = self.create(treebank=treebank, sent_id=sent_id, text=text, comments=comments)
        return sentence

class Sentence(models.Model):
    class Meta:
        unique_together = ['sent_id', 'text']

    treebank = models.ForeignKey(Treebank, on_delete=models.CASCADE)
    sent_id = models.CharField(max_length=30)
    text = models.TextField()
    comments = models.JSONField(blank=True)

    objects = SentenceManager()

    def __str__(self):
        return self.sent_id

class AnnotationManager(models.Manager):
    def create_annotation(self, annotator, sentence, cats, notes=''):
        annotation = self.create(annotator=annotator, sentence=sentence, cats=cats, notes=notes)
        return annotation

class Annotation(models.Model):
    annotator = models.ForeignKey(User, on_delete=models.CASCADE)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    cats = models.JSONField()
    notes = models.TextField()

    objects = AnnotationManager()

    def __str__(self):
        return '%s by %s' % (self.sentence.sent_id, self.annotator)