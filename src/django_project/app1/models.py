from django.db import models
from django.contrib.auth.models import User

class Treebank(models.Model):
    title = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.title

class SentenceManager(models.Manager):
    def create_sentence(self, treebank, sent_id, text, comments={}):
        sentence = self.create(treebank=treebank, sent_id=sent_id, text=text, comments=comments)
        return sentence

class Sentence(models.Model):
    treebank = models.ForeignKey(Treebank, on_delete=models.CASCADE)
    #TODO: make sent_id & text composite key together
    sent_id = models.CharField(max_length=30)
    text = models.TextField()
    comments = models.JSONField(blank=True)

    objects = SentenceManager()

    def __str__(self):
        return self.sent_id

class Annotation(models.Model):
    annotator = models.ForeignKey(User, on_delete=models.CASCADE)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    cats = models.JSONField()
    notes = models.TextField(blank=True)