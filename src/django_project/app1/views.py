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
from django.views.decorators.csrf import csrf_exempt

# may need to deexempt
@csrf_exempt
def error(request):
    error = None
    if request.method == 'POST':
        data = request.POST
        cells = json.loads(data['cells'])
        sent_id, text = data['sent_id'], data['text']
        error = conllu.get_errors(sent_id, text, cells)
    return render(request, 'error.html', {'error': error})

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
                treebanks_filtered = Treebank.objects.filter(title=request.POST['title'])
                if len(treebanks_filtered) == 0:
                    error = True
                    message = 'No treebank with that title.'
                else:
                    treebank_t = treebanks_filtered[0]
                    for sentence in sentences:
                        # Saving Sentence objects
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

def help(request):
    return render(request, 'help.html')

@login_required
def test(request):
    context = {}
    return render(request, 'test.html', context)

@login_required
def view_treebanks(request):
    treebanks = Treebank.objects.all()
    context = {'treebanks': treebanks}
    return render(request, 'view_treebanks.html', context)

@login_required
def view_treebank(request, treebank):
    message = ''
    treebank_selected = Treebank.objects.get_treebank_from_url(treebank)
    if treebank_selected == None: message = 'There is no treebank with that title.'
    sentences = Sentence.objects.filter(treebank=treebank_selected)
    context = {'sentences': sentences, 'message': message, 'treebank': treebank_selected}
    return render(request, 'view_treebank.html', context)

def replace_path(current_path, type, number=None):
    path_split = current_path.split('/')
    new_path = '/'.join(path_split[:3]) + '/'
    current_number = int(path_split[-1])
    number_to_go = current_number
    if type == 'previous':
        if current_number > 0: number_to_go = current_number - 1
    elif type == 'next':
        number_to_go = current_number + 1
    elif type == 'go': number_to_go = number
    return new_path + str(number_to_go)

import json
@login_required
def annotate(request, treebank, order):
    sentence, message, annotation, errors, cats = None, None, None, None, None
    treebank_selected = Treebank.objects.get_treebank_from_url(treebank)
    if treebank_selected == None: message = 'There is no treebank with that title.'
    else:
        sentences_filtered = Sentence.objects.filter(treebank=treebank_selected, order=order)
        if len(sentences_filtered) == 0:
            message = 'There is no sentence with that ID.'
        else:
            sentence = sentences_filtered[0]
            annotations_filtered = Annotation.objects.filter(annotator=request.user, sentence=sentence)
            if len(annotations_filtered) == 1: annotation = annotations_filtered[0]
            else:
                dummy_user = User.objects.get(username=DUMMY_USER_NAME)
                annotation = Annotation.objects.get(annotator=dummy_user, sentence=sentence)
    if not message:
        if request.method == "POST":
            data = request.POST['data']
            notes = request.POST['notes']
            word_lines = json.loads(data)
            annotation.notes = notes
            if request.user == annotation.annotator:
                annotation.save()
                anno_t = annotation
            else:
                anno_t = Annotation.objects.create_annotation(request.user, sentence, notes)
            for key in word_lines.keys():
                line_t = word_lines[key]
                id_f, form_f, lemma, upos, xpos, feats, head, deprel, deps, misc = key, line_t['form'], line_t['lemma'], line_t['upos'], line_t['xpos'], line_t['feats'], line_t['head'], line_t['deprel'], line_t['deps'], line_t['misc']
                wl_filtered = Word_Line.objects.filter(annotation=anno_t, id_f=id_f)
                if len(wl_filtered) == 0:
                    word_line_t = Word_Line.objects.create_word_line(anno_t, id_f, form_f, lemma, upos, xpos, feats, head, deprel, deps, misc)
                else:
                    wl_t = wl_filtered[0]
                    wl_t.form_f, wl_t.lemma, wl_t.upos, wl_t.xpos, wl_t.feats, wl_t.head, wl_t.deprel, wl_t.deps, wl_t.misc = form_f, lemma, upos, xpos, feats, head, deprel, deps, misc
                    wl_t.save()
            current_path = request.path
            button_type = request.POST['type']
            if button_type == 'go': number = request.POST['number']
            else: number = None
            return redirect(replace_path(current_path, button_type, number))
        elif request.method == "GET":
            word_lines_selected = Word_Line.objects.filter(annotation=annotation)
            cats = {}
            for word_line in word_lines_selected:
                id_f = word_line.id_f
                cats[id_f] = {'form': word_line.form_f, 'lemma': word_line.lemma, 'upos': word_line.upos, 'xpos': word_line.xpos, 'feats': word_line.feats, 'head': word_line.head, 'deprel': word_line.deprel, 'deps': word_line.deps, 'misc': word_line.misc}
            errors = conllu.get_errors(sentence.sent_id, sentence.text, cats)
            cats = json.dumps(cats)
    context = {'sentence': sentence, 'message': message, 'annotation': annotation, 'cats': cats, 'errors': errors}
    return render(request, 'annotate.html', context)

@login_required
def search(request):
    message = None
    if request.method == "POST":
        data = request.POST
        if 'type_select' not in data.keys():
            message = 'You need to select a type.'
        else:
            search_type = data['type_select']
            search_query = data['search']
            if 'regex' in data.keys():
                regexp = True
            data = {1:2, 3:4}
            return redirect('search_result')
    elif request.method == "GET":
        pass
    context = {'message': message}
    return render(request, 'search.html', context)

@login_required
def search_result(request, x):
    context = {'1':x}
    return render(request, 'search_result.html', context)