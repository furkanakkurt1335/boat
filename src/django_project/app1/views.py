from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as login_f, logout as logout_f, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UploadFileForm, TreebankForm, SentenceForm, AnnotationForm
from .models import SentenceManager, Treebank, Sentence, Annotation
from . import conllu

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            print(form)
    elif request.method == 'GET':
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
        print(request.POST['title'])
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
                    user = request.user
                    cats = {}
                    for key in sentence.keys():
                        if key not in ['sent_id', 'text', 'comments']: cats[key] = sentence[key]
                    anno_t = Annotation.objects.create_annotation(user, sent_t, cats)
                    anno_t.save()
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
    treebanks = Treebank.objects.all()
    treebank_selected = None
    for treebank_t in treebanks:
        if treebank_t.title.replace(' ', '-') == treebank: treebank_selected = treebank_t
    sentences = Sentence.objects.filter(treebank=treebank_selected)
    context = {'sentences': sentences}
    return render(request, 'view_treebank.html', context)

# @login_required
# def annotate(request, ):
#     context = {}
#     return render(request, 'test.html', context)