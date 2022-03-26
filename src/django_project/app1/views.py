from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login as login_f, logout as logout_f, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UploadFileForm, TreebankForm, SentenceForm, AnnotationForm
from .models import SentenceManager, Treebank, Sentence, Annotation, Word_Line
from . import conllu
from django_project.settings import DUMMY_USER_NAME, DUMMY_USER_PW

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            print(form)
    elif request.method == 'GET':
        if request.user.is_active:
            return redirect('profile')
        form = UserCreationForm()
        return render(request, 'register.html')
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login_f(request, user)
                return redirect('profile')
            else:
                return redirect('login')
        else:
            return redirect('login')
    elif request.method == 'GET':
        if request.user.is_active:
            return redirect('profile')
        form = AuthenticationForm()
        return render(request, 'login.html')
    return render(request, 'login.html')

def index(request):
    if request.user == 'AnonymousUser':
        return redirect('login')
    else:
        return redirect('profile')

@login_required
def logout(request):
    if request.user != 'AnonymousUser':
        logout_f(request)
    return redirect('login')

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required
def upload_file(request):
    treebanks = Treebank.objects.all()
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            is_valid_format = conllu.validate_uploaded_file(file)
            if is_valid_format:
                error = False
                sentences = conllu.parse_file(file)
                for sentence in sentences:
                    # Saving Sentence objects
                    treebanks_filtered = Treebank.objects.filter(title=request.POST['title'])
                    if len(treebanks_filtered) == 0:
                        error = True
                        message = 'No treebank with that title.'
                        break
                    else: treebank_t = treebanks_filtered[0]
                    sent_id_t = sentence['sent_id']
                    text_t = sentence['text']
                    if 'comments' in sentence.keys():
                        comments_t = sentence['comments']
                    else: comments_t = {}
                    try:
                        sent_t = Sentence.objects.create_sentence(treebank_t, sent_id_t, text_t, comments_t)
                        sent_t.save()
                    except: continue # duplicate

                    # Saving Annotation objects
                    user_selected = User.objects.filter(username=DUMMY_USER_NAME)
                    if len(user_selected) == 0:
                        user = User()
                        user.username = DUMMY_USER_NAME
                        user.password = DUMMY_USER_PW
                        user.save()
                    else: user = user_selected[0]
                    cats = {}
                    for key in sentence.keys():
                        if key not in ['sent_id', 'text', 'comments']: cats[key] = sentence[key]
                    anno_t = Annotation.objects.create_annotation(user, sent_t)
                    anno_t.save()
                    for key in cats.keys():
                        line_t = cats[key]
                        id_f, form_f, lemma, upos, xpos, feats, head, deprel, deps, misc = key, line_t['form'], line_t['lemma'], line_t['upos'], line_t['xpos'], line_t['feats'], line_t['head'], line_t['deprel'], line_t['deps'], line_t['misc']
                        word_line_t = Word_Line.objects.create_word_line(anno_t, id_f, form_f, lemma, upos, xpos, feats, head, deprel, deps, misc)
                if not error: message = 'You have uploaded a file successfully.'
            else: message = 'The file was not in the correct conllu format.'
            return render(request, 'upload_file.html', {'form': UploadFileForm(), 'message': message, 'treebanks': treebanks})
    else:
        form = UploadFileForm()
    return render(request, 'upload_file.html', {'form': form, 'treebanks': treebanks})

@login_required
def create_treebank(request):
    if request.method == 'POST':
        form = TreebankForm(request.POST)
        if form.is_valid():
            form.save()
            message = 'You have created a treebank successfully.'
        else: message = 'The treebank was not created.'
        return render(request, 'create_treebank.html', {'form': TreebankForm(), 'message': message})
    else:
        form = TreebankForm()
    return render(request, 'create_treebank.html', {'form': form})

@login_required
def test(request):
    context = {}
    return render(request, 'test.html', context)

@login_required
def view_treebank(request, treebank):
    message = ''
    treebank_selected = Treebank.objects.get_treebank_from_url(treebank)
    if treebank_selected == None: message = 'There is no treebank with that title.'
    sentences = Sentence.objects.filter(treebank=treebank_selected)
    context = {'sentences': sentences, 'message': message}
    return render(request, 'view_treebank.html', context)

def replace_path(current_path, type, number=None):
    path_split = current_path.split('/')
    new_path = '/'.join(path_split[:3]) + '/'
    current_number = int(path_split[-1])
    number_to_go = current_number
    if type == 'previous':
        if current_number > 0: number_to_go = current_number - 1
    elif type == 'next':
        number_to_go = 5
        number_to_go = current_number + 1
    elif type == 'go': number_to_go = number
    return new_path + str(number_to_go)

import json
@login_required
def annotate(request, treebank, id):
    sentence, message, annotation, errors = None, None, None, None
    treebank_selected = Treebank.objects.get_treebank_from_url(treebank)
    if treebank_selected == None: message = 'There is no treebank with that title.'
    else:
        sentences_filtered = Sentence.objects.filter(treebank=treebank_selected)
        if id < len(sentences_filtered):
            sentence = sentences_filtered[id]
            annotations_filtered = Annotation.objects.filter(annotator=request.user, sentence=sentence)
            if len(annotations_filtered) == 1: annotation = annotations_filtered[0]
            else:
                annotation_else = Annotation.objects.filter(sent_id=sentence.sent_id)[0]
                annotation = Annotation.objects.create_annotation(annotator=request.user, sentence=sentence, cats=annotation_else.cats)
    if request.method == "POST":
        data = request.POST['data']
        notes = request.POST['notes']
        annotation.cats = json.loads(data)
        annotation.notes = notes
        annotation.save()
        current_path = request.path
        button_type = request.POST['type']
        if button_type == 'go': number = request.POST['number']
        else: number = None
        return redirect(replace_path(current_path, button_type, number))
    else:
        errors = conllu.get_errors(sentence.sent_id, sentence.text, annotation.cats)
        annotation.cats = json.dumps(annotation.cats)
    context = {'sentence': sentence, 'message': message, 'annotation': annotation, 'errors': errors}
    return render(request, 'annotate.html', context)

@login_required
def search(request):
    return render(request, 'search.html')