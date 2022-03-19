import re

class Doc:
    def __init__(self, filepath):
        SENTENCE_SPLIT = r'\n\n+'
        DOC_ID = r'newdoc id\s*=\s*(\w+)\s*$'
        SENT_ID = r'sent_id\s*=\s*(.+)\s*$'
        TEXT = r'text\s*=\s*(.+)\s*$'

        content = open(filepath, 'r', encoding='utf-8').read()

        self.filepath = filepath
        self.sentences = []

        sents = re.split(SENTENCE_SPLIT, content)
        for sentence_id, sentence in enumerate(sents):
            if not sentence.strip(): continue # if sentence is empty due to last or first lines
            sentence = sents[sentence_id]
            sent_id = 'not_found'
            m = re.search(SENT_ID, sentence, flags=re.MULTILINE)
            if m: sent_id = m.group(1)

            doc_id = 'not_found'
            m = re.search(DOC_ID, sentence, flags=re.MULTILINE)
            if m: doc_id = m.group(1)

            text = 'not_found'
            m = re.search(TEXT, sentence, flags=re.MULTILINE)
            if m: text = m.group(1)

            # removes hashtagged lines
            empty_lines = 0
            for l in sentence.splitlines():
                if not l.startswith('#'): break
                empty_lines += 1

            words = sentence.splitlines()[empty_lines:]

            self.sentences.append(Sentence(doc_id, sent_id, text, words))

    def write(self):
        content = ""
        for sentence in self.sentences:
            content += '# sent_id = ' + sentence.sent_id + '\n'
            content += '# text = ' + sentence.text + '\n'
            for word in sentence.words:
                content += '\t'.join(word.get_list()) + '\n'
            content += '\n'
        open(self.filepath, 'w', encoding='utf-8').write(content)

class Sentence:
    def __init__(self, doc_id, sent_id, text, words):
        self.text = text
        self.sent_id = sent_id
        self.sent_address = 'n' + str(sent_id)
        self.doc_id = doc_id
        self.words = []
        for word in words:
            w = Word(word, self.sent_address)
            self.words.append(w)

    def get_head(self):
        for word in self.words:
            if word.cats['head'] == '0': return word.address()
            # if word.head == '0': return word.address()
        return 'Null'

    def get_raw(self):
        content = '# sent_id = ' + self.sent_id + '\n'
        content += '# text = ' + self.text + '\n'
        for word in self.words:
            content += '\t'.join(word.get_list()) + '\n'
        content += '\n'
        return content

class Word:
    def __init__(self, word, sa):
        items = word.split('\t')

        self.sent_add = sa
        self.cats = dict()
        cats_t = ['id', 'form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc']
        for i in range(10):
            self.cats[cats_t[i]] = items[i]
        self.unitword = False
        if '-' in self.cats['id']:
            self.unitword = True

    def get_list(self):
        l_t = []
        for key in self.cats.keys():
            l_t.append(self.cats[key])
        return l_t

    def address(self):
        return self.sent_add + '-' + self.cats['id']