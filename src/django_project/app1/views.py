from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as login_f, logout as logout_f, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, TreebankForm
from .models import Treebank, Sentence, Annotation, Word_Line, ExtendUser
from . import conllu
from django_project.settings import DUMMY_USER_NAME, DUMMY_USER_PW
from django.views.decorators.csrf import csrf_exempt

@login_required
def preferences(request):
    context = {}
    if request.method == 'POST':
        graph_selection = request.POST['graph_select']
        eu = ExtendUser.objects.get(user=request.user)
        eu.preferences['graph'] = graph_selection
        eu.save()
        context['message'] = 'Your preferences were saved successfully.'
    elif request.method == 'GET':
        context['graph_preference'] = ExtendUser.objects.get(user=request.user).preferences['graph']
    return render(request, 'preferences.html', context)

def sort_word_lines(word_lines):
    ret_l = []
    for i in range(1, len(word_lines)*5):
        dash_filtered = word_lines.filter(id_f=f'{i}-{i+1}')
        if len(dash_filtered) == 1: ret_l.append(dash_filtered[0])
        direct_filtered = word_lines.filter(id_f=f'{i}')
        if len(direct_filtered) == 1: ret_l.append(direct_filtered[0])
    return ret_l

@csrf_exempt
def download_conllu(request):
    content = None
    if request.method == 'POST':
        treebank_title = request.POST['treebank_title']
        treebank = Treebank.objects.get_treebank_from_title(treebank_title)
        all_sentences = Sentence.objects.filter(treebank=treebank)
        content = ''
        for sentence_t in all_sentences:
            annotations_t = Annotation.objects.filter(annotator=request.user, sentence=sentence_t)
            for annotation_t in annotations_t:
                word_lines_t = Word_Line.objects.filter(annotation=annotation_t)
                if len(word_lines_t) != 0:
                    word_lines_sorted = sort_word_lines(word_lines_t)
                    content += f'# sent_id = {sentence_t.sent_id}\n'
                    content += f'# text = {sentence_t.text}\n'
                for word_line_t in word_lines_sorted:
                    content += f'{word_line_t.id_f}\t{word_line_t.form}\t{word_line_t.lemma}\t{word_line_t.upos}\t{word_line_t.xpos}\t{word_line_t.feats}\t{word_line_t.head}\t{word_line_t.deprel}\n{word_line_t.deps}\t{word_line_t.misc}\n'
                content += '\n'
    return render(request, 'download_conllu.html', {'content': content})

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

@csrf_exempt
def ud_graph(request):
    graph = None
    if request.method == 'POST':
        from .ud_graph import Sentence as uds
        from .ud_graph import get_ud_graph
        data = request.POST
        cells = json.loads(data['cells'])
        field_l = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps']
        words = list()
        for key in cells.keys():
            word_t = key + '\t'
            for field in field_l:
                word_t += cells[key][field] + '\t'
            word_t += cells[key]['misc']
            words.append(word_t)
        sent_id, text = data['sent_id'], data['text']
        sent_t = uds(sent_id, text, words)
        graph = get_ud_graph(sent_t)
    return render(request, 'ud_graph.html', {'graph': graph})

@csrf_exempt
def spacy(request):
    graph = None
    if request.method == 'POST':
        from spacy import displacy
        data = request.POST
        cells = json.loads(data['cells'])
        manual = {"words": [], "arcs": [], "lemmas": []}
        dep_count = 0
        for key in cells.keys():
            word = cells[key]
            if '-' in key: continue
            manual['words'].append({"text": word['form'], "tag": word['upos'], "lemma": key})
            if word['deprel'] == '_' or word['head'] in ['_', '0']: continue
            head_int = int(word['head'])-1
            if int(key) > head_int:
                direction = 'left'
                start, end = head_int, int(key)
            else:
                direction = 'right'
                end, start = head_int, int(key)
            manual['arcs'].append({
                "start": start, "end": end, "label": word['deprel'], "dir": direction
            })
            dep_count += 1
        if dep_count == 0:
            graph = ''
        else:
            graph = displacy.render(docs=manual, style="dep", manual=True, options={'compact':'True', 'add_lemma': 'True', 'distance': 100})
    return render(request, 'spacy.html', {'graph': graph})

def register(request):
    message = None
    if request.method == 'POST':
        data = request.POST
        if data['password1'] == data['password2']:
            new_user = User.objects.create_user(username=data['username'], password=data['password1'], email=data['email'], first_name=data['first_name'], last_name=data['last_name'])
            return redirect('login')
        else: 
            message = 'The passwords do not match.'
    elif request.method == 'GET':
        if request.user.is_active:
            return redirect('profile')
        return render(request, 'register.html')
    return render(request, 'register.html', {'message': message})

def login(request):
    if request.method == 'POST':
        data = request.POST
        user = authenticate(username=data['username'], password=data['password'])
        if user is not None:
            if len(ExtendUser.objects.filter(user=user)) == 0:
                extenduser_t = ExtendUser()
                extenduser_t.user = user
                extenduser_t.preferences = {'graph': 'conllu.js', "error_condition": "shown", "current_columns": ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"]}
                extenduser_t.save()
            login_f(request, user)
            return redirect('profile')
        else:
            return redirect('login')
    elif request.method == 'GET':
        if request.user.is_active:
            return redirect('profile')
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
                            id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc = key, line_t['form'], line_t['lemma'], line_t['upos'], line_t['xpos'], line_t['feats'], line_t['head'], line_t['deprel'], line_t['deps'], line_t['misc']
                            word_line_t = Word_Line.objects.create_word_line(anno_t, id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc)
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
def view_treebank(request, treebank, page):
    message = ''
    treebank_selected = Treebank.objects.get_treebank_from_url(treebank)
    if treebank_selected == None: message = 'There is no treebank with that title.'
    context = {'message': message, 'treebank': treebank_selected, 'page': page}
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
        eu = ExtendUser.objects.get(user=request.user)
        if request.method == "POST":
            data = request.POST['data']
            data_changed = request.POST['data_changed']
            current_columns = request.POST['current_columns']
            error_condition = request.POST['error_condition']
            notes = request.POST['notes']
            status = request.POST['status']
            word_lines = json.loads(data)
            annotation.notes = notes
            if data_changed == 'true':
                if request.user == annotation.annotator:
                    annotation.save()
                    anno_t = annotation
                else:
                    anno_t = Annotation.objects.create_annotation(request.user, sentence, notes, status)
                for key in word_lines.keys():
                    line_t = word_lines[key]
                    id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc = key, line_t['form'], line_t['lemma'], line_t['upos'], line_t['xpos'], line_t['feats'], line_t['head'], line_t['deprel'], line_t['deps'], line_t['misc']
                    wl_filtered = Word_Line.objects.filter(annotation=anno_t, id_f=id_f)
                    if len(wl_filtered) == 0:
                        Word_Line.objects.create_word_line(anno_t, id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc)
                    else:
                        wl_t = wl_filtered[0]
                        wl_t.form, wl_t.lemma, wl_t.upos, wl_t.xpos, wl_t.feats, wl_t.head, wl_t.deprel, wl_t.deps, wl_t.misc = form, lemma, upos, xpos, feats, head, deprel, deps, misc
                        wl_t.save()
            eu.preferences['current_columns'] = current_columns
            eu.preferences['error_condition'] = error_condition
            eu.save()
            current_path = request.path
            button_type = request.POST['type']
            if button_type == 'go': number = request.POST['number']
            elif button_type == 'profile': return redirect('profile')
            else: number = None
            return redirect(replace_path(current_path, button_type, number))
        elif request.method == "GET":
            word_lines_selected = Word_Line.objects.filter(annotation=annotation)
            cats = {}
            for word_line in word_lines_selected:
                id_f = word_line.id_f
                cats[id_f] = {'form': word_line.form, 'lemma': word_line.lemma, 'upos': word_line.upos, 'xpos': word_line.xpos, 'feats': word_line.feats, 'head': word_line.head, 'deprel': word_line.deprel, 'deps': word_line.deps, 'misc': word_line.misc}
            errors = conllu.get_errors(sentence.sent_id, sentence.text, cats)
            cats = json.dumps(cats)
    context = {'sentence': sentence, 'message': message, 'annotation': annotation, 'cats': cats, 'errors': errors, 'graph_preference': eu.preferences['graph'], 'error_condition': eu.preferences['error_condition'], 'current_columns': eu.preferences['current_columns']}
    return render(request, 'annotate.html', context)

@login_required
def search(request):
    message = None
    if request.method == "POST":
        data = request.POST
        queries = {}
        count = 1
        while 1:
            if f'input_{count}' not in data.keys(): break
            if f'type_{count}' in data.keys() and data[f'input_{count}'] != '':
                queries[count] = {}
                queries[count]['type'] = data[f'type_{count}']
                queries[count]['input'] = data[f'input_{count}']
            count += 1
        return render(request, 'search.html', {'queries': json.dumps(queries)})
    elif request.method == "GET":
        pass
    context = {'message': message}
    return render(request, 'search.html', context)

@login_required
def my_annotations(request):
    message = None
    if request.method == "POST":
        pass
    elif request.method == "GET":
        pass
    context = {'message': message, 'username': request.user.id}
    return render(request, 'my_annotations.html', context)