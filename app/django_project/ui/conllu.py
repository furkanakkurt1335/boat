import re, subprocess, os, sys, json
from pathlib import Path


script_dir = Path(__file__).parent
THISDIR = os.path.dirname(os.path.realpath(__file__))

language_ids_path = script_dir / 'language_ids.json'
with language_ids_path.open('r', encoding='utf-8') as f:
    LANGUAGES = json.load(f)

def validate_uploaded_file(f):
    file_text = None
    try:
        for chunk in f.chunks():
            if file_text == None: file_text = chunk
            else: file_text += chunk
        file_text = file_text.decode('utf-8')
        sentence_pattern = r'(?:#.+=.*\n)+(?:(?:.+\t){9}.+\n)+'
        file_text = re.sub(sentence_pattern, '', file_text)
    except: return False
    if file_text.strip() == '': return True
    else: return False

def parse_file(f):
    file_text = f.read()
    # for chunk in f.chunks():
    #     if file_text == None: file_text = chunk
    #     else: file_text += chunk
    # file_text = file_text.decode('utf-8')
    sentence_pattern = r'(?:#.+=.+\n)+(?:(?:.+\t){9}.+\n)+'
    sentences_found = re.findall(sentence_pattern, file_text)
    sentences = []
    comment_pattern = r'#(.+)=(.*)'
    cats = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc']
    cats_pattern = r'(?:.+\t){9}.+'
    for curr_sentence in sentences_found:
        sentence = {}
        for line in curr_sentence.split('\n'):
            if line.startswith('#'):
                comment_found = re.match(comment_pattern, line)
                if comment_found and len(comment_found.groups()) == 2:
                    key, value = comment_found.group(1).strip(), comment_found.group(2).strip()
                    print(key, value)
                    if key not in ['sent_id', 'text']:
                        if 'comments' not in sentence.keys():
                            sentence['comments'] = dict()
                        if not value:
                            continue
                        sentence['comments'][key] = value
                    else:
                        sentence[key] = value
            else:
                cats_found = re.match(cats_pattern, line)
                if cats_found:
                    cats_t = cats_found.group().strip().split('\t')
                    id_t = cats_t[0]
                    sentence[id_t] = dict()
                    for i in range(1, 10):
                        cat_t = cats_t[i]
                        sentence[id_t][cats[i-1]] = cat_t
        sentences.append(sentence)
    return sentences

def get_errors(sent_id, text, content, language):
    input_str = f'# sent_id = {sent_id}\n'
    input_str += f'# text = {text}\n'
    order = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps'] # id & misc removed
    con_keys = list(content.keys())
    keys = []
    for key in range(1, len(con_keys)*2):
        if f'{key}-{key+1}' in con_keys:
            keys.append(f'{key}-{key+1}')
        if f'{key}' in con_keys:
            keys.append(f'{key}')
    for key in keys:
        input_str += f'{key}\t' # id
        for i in range(8):
            input_str += f'{content[key][order[i]]}\t'
        input_str += f'{content[key]["misc"]}\n' # misc
    input_str += '\n'
    # get validation script if not exists, otherwise update it
    tools_dir = script_dir / 'tools'
    tools_url = 'https://github.com/UniversalDependencies/tools.git'
    if not tools_dir.exists():
        subprocess.run(['git', 'clone', tools_url, tools_dir])
    else:
        subprocess.run(['git', '-C', tools_dir, 'pull'])
    validation_script = tools_dir / 'validate.py'
    val_str = subprocess.run([sys.executable, validation_script, '--lang', LANGUAGES[language]], 
                             input=input_str, encoding='utf-8', capture_output=True).stderr
    new_val_str = str()
    error_pattern = '\[Line (\d+) Sent .+\]: \[L\d .+\] (.*)$'
    for line in val_str.split('\n'):
        error_search = re.search(error_pattern, line)
        if error_search:
            node_t, error_t = error_search.group(1), error_search.group(2)
            new_val_str += 'ID {n}: {err}\n'.format(n=keys[int(node_t)-2-1], err=error_t)
        else:
            break
    return new_val_str
