import os, sys
with open(f'{os.path.dirname(os.path.realpath(__file__))}/{sys.argv[1]}', 'r', encoding='utf-8') as f:
    data = f.readlines()
new_data = ''
for line in data:
    if not (line.startswith('#') or line == '' or '-' in line.split('\t')[0]):
        tokens = line.split('\t')
        new_tokens = list()
        for i, token in enumerate(tokens): # deletes xpos, feats, head, deprel
            if i in [4, 5, 6, 7]: new_tokens.append('_')
            else: new_tokens.append(token)
        new_line = '\t'.join(new_tokens)
        new_data += f'{new_line}'
    else: new_data += f'{line}'
with open('new_data.conllu', 'w', encoding='utf-8') as f:
    f.write(new_data)