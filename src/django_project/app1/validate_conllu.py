import re

def validate_uploaded_file(f):
    file_text = None
    try:
        for chunk in f.chunks():
            if file_text == None: file_text = chunk
            else: file_text += chunk
        file_text = file_text.decode('utf-8')
        sentence_pattern = r'(#.+=.+\n){2}((.+\t){9}.+\n)+'
        file_text = re.sub(sentence_pattern, '', file_text)
    except: return False
    if file_text.strip() == '': return True
    else: return False