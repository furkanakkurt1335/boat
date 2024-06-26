import json, re, os
from pathlib import Path
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as login_f, logout as logout_f, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, TreebankForm
from .models import Treebank, Sentence, Annotation, Word_Line, ExtendUser
from . import conllu
from django_project.settings import DUMMY_USER_NAME, DUMMY_USER_PW
from django.views.decorators.csrf import csrf_exempt
# from spacy.lang.en import English
# from spacy import displacy

# nlp = English()
# tokenizer = nlp.tokenizer

import logging

logger = logging.getLogger(__name__)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
script_dir = Path(__file__).parent

def compute_anno_agr(annos):
    # anno_l = []
    # for anno in annos:
    # if 'dummy_user' not in anno.annotator.username: anno_l.append(anno)
    wordlines = []
    for anno in annos:
        wordlines.append(Word_Line.objects.filter(annotation=anno))
    wl_d = {}
    for wl_l in wordlines:
        for wl in wl_l:
            if wl.id_f not in wl_d.keys():
                wl_d[wl.id_f] = [wl]
            else:
                wl_d[wl.id_f].append(wl)
    score_sum, count = 0, 0
    for key in wl_d.keys():
        if '-' in key:
            return -1  # split lemmas forbidden (for now)
        wls = wl_d[key]
        wl_len = len(wls)
        if wl_len <= 1:
            continue
        for i in range(wl_len):
            for j in range(i+1, wl_len):
                score_t = 0
                if wls[i].form == wls[j].form and wls[i].lemma == wls[j].lemma:
                    # agreement_score += 1
                    if wls[i].upos == wls[j].upos:
                        score_t += 1
                    else:
                        print('UPOS', wls[i].upos, wls[j].upos)
                    # if wls[i].xpos == wls[j].xpos:
                    #     agreement_score += 1
                    if wls[i].feats == wls[j].feats:
                        score_t += 1
                    else:
                        print('FEATS', wls[i].feats, wls[j].feats)
                    if wls[i].head == wls[j].head:
                        score_t += 1
                    else:
                        print('HEAD', wls[i].head, wls[j].head)
                    if wls[i].deprel == wls[j].deprel:
                        score_t += 1
                    else:
                        print('DEPREL', wls[i].deprel, wls[j].deprel)
                    # if wls[i].deps == wls[j].deps:
                    #     agreement_score += 1
                score_sum += score_t
                count += 1
    return score_sum / (count * 4)


@login_required
def compute_agreement(request):
    context = {}
    tb_names = Treebank.objects.all()
    context['tbs'] = tb_names
    if request.method == 'POST':
        agreement_score_sum = 0
        tb_name = request.POST['title']
        context['tb_name'] = tb_name
        sents = Sentence.objects.filter(treebank__title=tb_name)
        anno_count = 0
        for sent in sents:
            annos = Annotation.objects.filter(sentence=sent)
            if len(annos) > 1:
                agreement_t = compute_anno_agr(annos)  # 2
                if agreement_t == -1:
                    continue
                agreement_score_sum += agreement_t
                anno_count += 1
        if anno_count == 0:
            context['score'] = 0
        else:
            context['score'] = agreement_score_sum / anno_count  # b/w 0-1
    return render(request, 'compute_agreement.html', context)


@login_required
def preferences(request):
    context = {}
    if request.method == 'POST':
        graph_selection = request.POST['graph_select']
        eu = ExtendUser.objects.get(user=request.user)
        eu.preferences['graph_preference'] = graph_selection
        eu.save()
        context['message'] = 'Your preferences were saved successfully.'
    elif request.method == 'GET':
        context['graph_preference'] = ExtendUser.objects.get(
            user=request.user).preferences['graph_preference']
    return render(request, 'preferences.html', context)


def sort_word_lines(word_lines):
    ret_l = []
    for i in range(1, len(word_lines)*5):
        dash_filtered = word_lines.filter(id_f=f'{i}-{i+1}')
        if len(dash_filtered) == 1:
            ret_l.append(dash_filtered[0])
        direct_filtered = word_lines.filter(id_f=f'{i}')
        if len(direct_filtered) == 1:
            ret_l.append(direct_filtered[0])
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
            annotations_t = Annotation.objects.filter(
                annotator=request.user, sentence=sentence_t)
            for annotation_t in annotations_t:
                word_lines_t = Word_Line.objects.filter(
                    annotation=annotation_t)
                if len(word_lines_t) != 0:
                    word_lines_sorted = sort_word_lines(word_lines_t)
                    content += f'# sent_id = {sentence_t.sent_id}\n'
                    content += f'# text = {sentence_t.text}\n'
                    if sentence_t.comments:
                        for key in sentence_t.comments.keys():
                            content += f'# {key} = {sentence_t.comments[key]}\n'
                for word_line_t in word_lines_sorted:
                    content += f'{word_line_t.id_f}\t{word_line_t.form}\t{word_line_t.lemma}\t{word_line_t.upos}\t{word_line_t.xpos}\t{word_line_t.feats}\t{word_line_t.head}\t{word_line_t.deprel}\t{word_line_t.deps}\t{word_line_t.misc}\n'
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
        field_l = ['form', 'lemma', 'upos', 'xpos',
                   'feats', 'head', 'deprel', 'deps']
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
        data = request.POST
        cells = json.loads(data['cells'])
        manual = {"words": [], "arcs": [], "lemmas": []}
        dep_count = 0
        for key in cells.keys():
            word = cells[key]
            if '-' in key:
                continue
            manual['words'].append(
                {"text": word['form'], "tag": word['upos'], "lemma": key})
            if word['deprel'] == '_' or word['head'] in ['_', '0']:
                continue
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
            graph = displacy.render(docs=manual, style="dep", manual=True, options={
                                    'compact': 'True', 'add_lemma': 'True', 'distance': 100})
    return render(request, 'spacy.html', {'graph': graph})


def register(request):
    message, data = [], {'username': '',
                         'first_name': '', 'last_name': '', 'email': ''}
    if request.method == 'POST':
        data = request.POST
        if data['username'] == '':
            message.append('Username was not filled.')
        if data['first_name'] == '':
            message.append('First name was not filled.')
        if data['last_name'] == '':
            message.append('Last name was not filled.')
        if data['email'] == '':
            message.append('Email was not filled.')
        if data['password1'] == '' or data['password2'] == '':
            message.append('Password empty.')
        elif data['password1'] != data['password2']:
            message.append('The passwords do not match.')
        if len(message) == 0:
            User.objects.create_user(
                username=data['username'], password=data['password1'], email=data['email'], first_name=data['first_name'], last_name=data['last_name'])
            return redirect('login')
    elif request.method == 'GET':
        if request.user.is_active:
            return redirect('home')
        return render(request, 'register.html')
    return render(request, 'register.html', {'message': message, 'data': data})


def login(request):
    message, data = [], {'username': ''}
    if request.method == 'POST':
        data = request.POST
        username, password = data['username'], data['password']
        if username == '':
            message.append('Username not filled.')
        if password == '':
            message.append('Password not filled.')
        if len(message) == 0:
            user = authenticate(
                username=username, password=password)
            if user is not None:
                if len(ExtendUser.objects.filter(user=user)) == 0:
                    extenduser_t = ExtendUser()
                    extenduser_t.user = user
                    extenduser_t.preferences = {'graph_preference': 1, "error_condition": True, "current_columns": [
                        "ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"]}
                    extenduser_t.save()
                login_f(request, user)
                return redirect('home')
            else:
                message.append('User not found with these credentials.')
        return render(request, 'login.html', {'message': message, 'data': data})
    elif request.method == 'GET':
        if request.user.is_active:
            return redirect('home')
    return render(request, 'login.html')


def about(request):
    if request.user == 'AnonymousUser':
        return redirect('login')
    else:
        return render(request, 'about.html')


def index(request):
    if request.user == 'AnonymousUser':
        return redirect('login')
    else:
        return redirect('home')


@login_required
def logout(request):
    if request.user != 'AnonymousUser':
        logout_f(request)
    return redirect('login')


@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})


@login_required
def home(request):
    return render(request, 'home.html')


@csrf_exempt
def parse_save_file(request):
    file_path = request.POST['file_path']
    file = open(file_path, 'r', encoding='utf-8')
    sentences = conllu.parse_file(file)
    treebanks_filtered = Treebank.objects.filter(
        title=request.POST['title'])
    treebank_t = treebanks_filtered[0]
    for sentence in sentences:
        # Saving Sentence objects
        sent_id_t = sentence['sent_id']
        text_t = sentence['text']
        if 'comments' in sentence.keys():
            comments_t = sentence['comments']
        else:
            comments_t = {}
        try:
            sent_t = Sentence.objects.create_sentence(
                treebank_t, sent_id_t, text_t, comments_t)
            sent_t.save()
        except:
            continue  # duplicate

        # Saving Annotation objects
        user_selected = User.objects.filter(
            username=DUMMY_USER_NAME)
        if len(user_selected) == 0:
            user = User()
            user.username = DUMMY_USER_NAME
            user.password = DUMMY_USER_PW
            user.save()
        else:
            user = user_selected[0]
        cats = {}
        for key in sentence.keys():
            if key not in ['sent_id', 'text', 'comments']:
                cats[key] = sentence[key]
        anno_t = Annotation.objects.create_annotation(
            user, sent_t)
        anno_t.save()
        for key in cats.keys():
            line_t = cats[key]
            id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc = key, line_t['form'], line_t['lemma'], line_t[
                'upos'], line_t['xpos'], line_t['feats'], line_t['head'], line_t['deprel'], line_t['deps'], line_t['misc']
            word_line_t = Word_Line.objects.create_word_line(
                anno_t, id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc)
    return render(request, 'parse_save_file.html')

@login_required
def upload_file(request):
    treebanks = Treebank.objects.all()
    context = {'form': UploadFileForm(), 'treebanks': treebanks}
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            is_valid_format = conllu.validate_uploaded_file(file)
            if is_valid_format:
                file = form.save()
                error = False
                if not error:
                    message = 'You have uploaded a file successfully.'
            else:
                message = 'The file was not in the correct conllu format.'
            context['message'], context['path'], context['treebank_title'] = message, file.file.path.replace('\\', '/'), request.POST['title']
    return render(request, 'upload_file.html', context)


@login_required
@csrf_exempt
def add_sentence(request):
    treebanks = Treebank.objects.all()
    context = {'treebanks': treebanks}
    if request.method == 'POST':
        treebank_title = request.POST['title']
        treebank = Treebank.objects.get_treebank_from_title(treebank_title)
        sent_count = len(Sentence.objects.filter(treebank=treebank))
        sent_id = f'{treebank_title}-{sent_count+1}'
        sentence = request.POST['sentence']
        if treebank == None:
            message = 'There is no treebank with that title.'
        else:
            sent_t = Sentence.objects.create_sentence(
                treebank, sent_id, sentence, {})
            # Saving Annotation objects
            user_selected = User.objects.filter(
                username=DUMMY_USER_NAME)
            if len(user_selected) == 0:
                user = User()
                user.username = DUMMY_USER_NAME
                user.password = DUMMY_USER_PW
                user.save()
            else:
                user = user_selected[0]
            cats = {}
            # tokens = [str(i) for i in tokenizer(sentence)]
            tokens = [str(i) for i in sentence.split()]
            anno_t = Annotation.objects.create_annotation(
                user, sent_t)
            anno_t.save()
            id_t = 1
            for token in tokens:
                id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc = id_t, token, token, '_', '_', '_', '_', '_', '_', '_'
                word_line_t = Word_Line.objects.create_word_line(
                    anno_t, id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc)
                id_t += 1
            message = 'You have added a sentence successfully.'
        context['message'] = message
    return render(request, 'add_sentence.html', context)

@csrf_exempt
def delete_sentence(request):
    if request.method == 'POST':
        sent_id = request.POST['sent_id']
        treebank_title = request.POST['title']
        treebank = Treebank.objects.get_treebank_from_title(treebank_title)
        sentence = Sentence.objects.get(sent_id=sent_id, treebank=treebank)
        sentence.delete()
        return render(request, 'delete_sentence.html', {'sent_id': sent_id, 'treebank_title': treebank_title})
    else:
        return render(request, 'delete_sentence.html', {'sent_id': ''})

@csrf_exempt
def edit_metadata(request):
    if request.method == 'POST':
        sent_id = request.POST['sent_id']
        treebank_title = request.POST['title']
        treebank = Treebank.objects.get_treebank_from_title(treebank_title)
        sentence = Sentence.objects.get(sent_id=sent_id, treebank=treebank)
        comments = json.loads(request.POST['metadata'])
        if '' in comments.keys():
            del comments['']
        sentence.comments = comments
        sentence.save()
        return render(request, 'edit_metadata.html', {'sent_id': sent_id, 'treebank_title': treebank_title, 'comments': comments})
    else:
        return render(request, 'edit_metadata.html', {'sent_id': '', 'treebank_title': '', 'comments': {}})

@csrf_exempt
def delete_treebank(request):
    if request.method == 'POST':
        tb_title = request.POST['treebank_title']
        Treebank.objects.get(title=tb_title).delete()
        return render(request, 'delete_treebank.html', {'treebank_title': tb_title})
    else:
        return render(request, 'delete_treebank.html', {'treebank_title': ''})


@login_required
def create_treebank(request):
    if request.method == 'POST':
        form = TreebankForm(request.POST)
        if form.is_valid():
            form.save()
            message = 'You have created a treebank successfully.'
        else:
            message = 'The treebank was not created.'
        return render(request, 'create_treebank.html', {'form': TreebankForm(), 'message': message})
    else:
        form = TreebankForm()
    language_ids_path = script_dir / 'language_ids.json'
    with language_ids_path.open('r', encoding='utf-8') as f:
        languages = json.load(f)
    language_l = list(languages.keys())
    return render(request, 'create_treebank.html', {'form': form, 'languages': language_l})


def help(request):
    return render(request, 'help.html')


@login_required
def test(request):
    context = {}
    return render(request, 'test.html', context)


@login_required
def view_treebanks(request):
    treebanks = Treebank.objects.all()
    tb_title_l = []
    tb_d = {}
    for tb in treebanks:
        tb_title_l.append(tb.title)
        tb_d[tb.title] = tb
    tb_title_l.sort()
    tb_ct_d = []
    for tb in tb_title_l:
        sent_l = Sentence.objects.filter(treebank=tb_d[tb])
        progress = 0
        for sent_t in sent_l:
            if len(Annotation.objects.filter(sentence=sent_t, status=2)) != 0:
                progress += 1
        if len(sent_l) == 0:
            progress = 0.0
        else:
            progress = int(progress / len(sent_l) * 100)
        tb_ct_d.append(
            {'title': tb, 'size': len(sent_l), 'progress': progress})
    context = {'tbs': tb_ct_d}
    return render(request, 'view_treebanks.html', context)


@login_required
def view_treebank(request, treebank):
    message = ''
    treebank_selected = Treebank.objects.get_treebank_from_url(treebank)
    if not treebank_selected:
        message = 'There is no treebank with that title.'
    context = {'message': message,
               'treebank_title': treebank_selected}
    return render(request, 'view_treebank.html', context)


def replace_path(current_path, type, number=None):
    path_split = current_path.split('/')
    new_path = '/'.join(path_split[:-1]) + '/'
    current_number = int(path_split[-1])
    number_to_go = current_number
    if type == 'previous':
        if current_number > 0:
            number_to_go = current_number - 1
    elif type == 'next':
        number_to_go = current_number + 1
    elif type == 'go':
        number_to_go = number
    return new_path + str(number_to_go)


@login_required
def annotate(request, treebank, order):
    print(request.POST)
    sentence, message, annotation, errors, cats, language = None, None, None, None, None, None
    treebank_selected = Treebank.objects.get_treebank_from_url(treebank)
    if not treebank_selected:
        message = 'There is no treebank with that title.'
        return render(request, 'annotate.html', {'message': message})
    else:
        language = treebank_selected.language
        sentences_filtered = Sentence.objects.filter(
            treebank=treebank_selected, order=order)
        if len(sentences_filtered) == 0:
            message = 'There is no sentence with that order in this treebank.'
            return render(request, 'annotate.html', {'message': message})
        else:
            sentence = sentences_filtered[0]
            annotations_filtered = Annotation.objects.filter(
                annotator=request.user, sentence=sentence)
            if len(annotations_filtered) == 1:
                annotation = annotations_filtered[0]
            else:
                dummy_user = User.objects.get(username=DUMMY_USER_NAME)
                annotation = Annotation.objects.get(
                    annotator=dummy_user, sentence=sentence)
    if not message:
        eu = ExtendUser.objects.get(user=request.user)
        if request.method == 'POST':
            data = request.POST['data']
            data_changed = request.POST['data_changed']
            current_columns = request.POST['current_columns'].split(',')
            for i in range(len(current_columns)):
                current_columns[i] = current_columns[i].lower()
            error_condition_t = request.POST['error_condition']
            if error_condition_t == "1":
                error_condition = 1
            else:
                error_condition = 0
            graph_preference = int(request.POST['graph_preference'])
            notes = request.POST['notes']
            status = int(request.POST['status'])
            word_lines = json.loads(data)
            annotation.status = status
            annotation.notes = notes
            button_type = request.POST['type']
            if data_changed == 'true' or button_type == 'save':
                if request.user == annotation.annotator:
                    annotation.save()
                    anno_t = annotation
                else:
                    anno_t = Annotation.objects.create_annotation(
                        request.user, sentence, notes, status)
                for key in word_lines.keys():
                    line_t = word_lines[key]
                    id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc = key, line_t['form'], line_t['lemma'], line_t[
                        'upos'], line_t['xpos'], line_t['feats'], line_t['head'], line_t['deprel'], line_t['deps'], line_t['misc']
                    wl_filtered = Word_Line.objects.filter(
                        annotation=anno_t, id_f=id_f)
                    if len(wl_filtered) == 0:
                        Word_Line.objects.create_word_line(
                            anno_t, id_f, form, lemma, upos, xpos, feats, head, deprel, deps, misc)
                    else:
                        wl_t = wl_filtered[0]
                        wl_t.form, wl_t.lemma, wl_t.upos, wl_t.xpos, wl_t.feats, wl_t.head, wl_t.deprel, wl_t.deps, wl_t.misc = form, lemma, upos, xpos, feats, head, deprel, deps, misc
                        wl_t.save()
            eu.preferences['current_columns'] = current_columns
            eu.preferences['error_condition'] = error_condition
            eu.preferences['graph_preference'] = graph_preference
            eu.save()
            current_path = request.path
            if button_type == 'go':
                number = request.POST['number']
            elif button_type == 'profile':
                return redirect('profile')
            elif button_type == 'home':
                return redirect('home')
            else:
                number = None
            return redirect(replace_path(current_path, button_type, number))
        elif request.method == 'GET':
            word_lines_selected = Word_Line.objects.filter(
                annotation=annotation)
            cats = {}
            for word_line in word_lines_selected:
                id_f = word_line.id_f
                cats[id_f] = {'form': word_line.form, 'lemma': word_line.lemma, 'upos': word_line.upos, 'xpos': word_line.xpos,
                              'feats': word_line.feats, 'head': word_line.head, 'deprel': word_line.deprel, 'deps': word_line.deps, 'misc': word_line.misc}
            errors = conllu.get_errors(sentence.sent_id, sentence.text, cats, language)
            cats = json.dumps(cats)
    autocomplete_d = {}
    if language:
        language_ids_path = script_dir / 'language_ids.json'
        with language_ids_path.open('r', encoding='utf-8') as f:
            languages = json.load(f)
        language_id = languages[language]
        data_dir = script_dir / 'tools/data'
        deprels_path = data_dir / 'deprels.json'
        with deprels_path.open('r', encoding='utf-8') as f:
            deprels = json.load(f)['deprels']
        autocomplete_d['DEPREL'] = list(deprels[language_id].keys())
        feats_path = data_dir / 'feats.json'
        with feats_path.open('r', encoding='utf-8') as f:
            feats = json.load(f)['features']
        lang_feats = feats[language_id]
        for key in lang_feats.keys():
            value_l = []
            feat_t = lang_feats[key]
            for l in ['uvalues', 'lvalues', 'unused_uvalues', 'unused_lvalues', 'evalues']:
                value_l.extend(feat_t[l])
            autocomplete_d[key] = value_l
    context = {
        'sentence': sentence,
        'message': message,
        'annotation': annotation,
        'cats': cats,
        'errors': errors,
        'graph_preference': eu.preferences['graph_preference'],
        'error_condition': eu.preferences['error_condition'],
        'current_columns': eu.preferences['current_columns'],
        'autocomplete_d': json.dumps(autocomplete_d),
        'language': language
    }
    return render(request, 'annotate.html', context)


@login_required
def search(request):
    message, context = None, {}
    if request.method == "POST":
        data = request.POST
        filled_input = False
        if data['title'] != 'Select treebank':
            queries = {}
            count = 1
            for key in data.keys():
                if key.startswith('input_'):
                    num_str = re.search('input_(\d+)', key).group(1)
                    if data[key] != '':
                        queries[count] = {}
                        queries[count]['type'] = data[f'type_{num_str}']
                        queries[count]['input'] = data[f'input_{num_str}']
                        if data[f'input_{num_str}'].strip() != '':
                            filled_input = True
                        count += 1
            if not filled_input:
                message = 'No input filled.'
                tb_names = Treebank.objects.all()
                context['tbs'] = tb_names
            else:
                return render(request, 'search.html', {'queries': json.dumps(queries), 'treebank_title': data['title']})
        else:
            message = 'No treebank selected.'
            tb_names = Treebank.objects.all()
            context['tbs'] = tb_names
    elif request.method == "GET":
        tb_names = Treebank.objects.all()
        context['tbs'] = tb_names
    context['message'] = message
    return render(request, 'search.html', context)


@login_required
def my_annotations(request):
    message = None
    if request.method == "POST":
        pass
    elif request.method == "GET":
        pass
    context = {'message': message,
               'username': request.user.id}
    return render(request, 'my_annotations.html', context)
