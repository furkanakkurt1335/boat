from spacy import displacy

def get_dep_graph(sentence):
    manual = {"words": [], "arcs": [], "lemmas": []}
    word_count_t = len(sentence.keys())
    dep_count = 0
    for i in range(len(sentence.keys())):
        word = sentence[sentence.keys()[i]]
        if '-' in word['id']: continue
        manual['words'].append({"text": word['form'], "tag": word['upos'], "lemma": word['id']})
        if word['deprel'] == '_' or word['head'] in ['_', '0']: continue
        head_int = int(word['head'])-1
        if i > head_int:
            direction = 'left'
            start, end = head_int, i
        else:
            direction = 'right'
            end, start = head_int, i
        manual['arcs'].append({
            "start": start, "end": end, "label": word['deprel'], "dir": direction
        })
        dep_count += 1
    if dep_count == 0: return ''

    return displacy.render(docs=manual, style="dep", manual=True, options={'compact':'True', 'add_lemma': 'True', 'distance': 100})