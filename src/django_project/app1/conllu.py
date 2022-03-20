import re

def validate_uploaded_file(f):
    file_text = None
    try:
        for chunk in f.chunks():
            if file_text == None: file_text = chunk
            else: file_text += chunk
        file_text = file_text.decode('utf-8')
        sentence_pattern = r'(?:#.+=.+\n)+(?:(?:.+\t){9}.+\n)+'
        file_text = re.sub(sentence_pattern, '', file_text)
    except: return False
    if file_text.strip() == '': return True
    else: return False

def parse_file(f):
    file_text = None
    for chunk in f.chunks():
        if file_text == None: file_text = chunk
        else: file_text += chunk
    file_text = file_text.decode('utf-8')
    sentence_pattern = r'(?:#.+=.+\n)+(?:(?:.+\t){9}.+\n)+'
    sentences_found = re.findall(sentence_pattern, file_text)
    sentences = []
    comment_pattern = r'#(.+)=(.+)'
    cats = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc']
    cats_pattern = r'(?:.+\t){9}.+'
    for curr_sentence in sentences_found:
        sentence = {}
        for line in curr_sentence.split('\n'):
            if line.startswith('#'):
                comment_found = re.match(comment_pattern, line)
                if comment_found:
                    if comment_found.group(1).strip() not in ['sent_id', 'text']:
                        if 'comments' in sentence.keys():
                            sentence['comments'] = dict()
                        sentence['comments'][comment_found.group(1).strip()] = comment_found.group(2).strip()
                    else:
                        sentence[comment_found.group(1).strip()] = comment_found.group(2).strip()
            else:
                cats_found = re.match(cats_pattern, line)
                if cats_found:
                    cats_t = cats_found.group().strip().split('\t')
                    id_t = cats_t[0]
                    sentence[id_t] = dict()
                    for i in range(9):
                        cat_t = cats_t[i]
                        sentence[id_t][cats[i]] = cat_t
        sentences.append(sentence)
    return sentences