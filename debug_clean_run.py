import sys
sys.path.append(r'c:\nagarikta')
from main import normalize_ocr_text, strip_field_prefix, strip_generic_leading_label, clean_field_text
import re

def debug(text, class_id):
    print('ORIG:', repr(text))
    t = normalize_ocr_text(text)
    print('normalize_ocr_text ->', repr(t))
    if ':' in t or ';' in t:
        after = re.split(r"[:;]", t)[-1].strip()
        print('after colon split ->', repr(after))
        t = after
    t2 = strip_field_prefix(t, class_id)
    print('after strip_field_prefix ->', repr(t2))
    t3 = strip_generic_leading_label(t2)
    print('after strip_generic_leading_label ->', repr(t3))
    print('clean_field_text ->', repr(clean_field_text(text, class_id)))

def debug_tokens(text, class_id):
    print('\n-- token debug --')
    orig = text
    t = normalize_ocr_text(text)
    if ':' in t or ';' in t:
        t = __import__('re').split(r"[:;]", t)[-1].strip()
    t = strip_field_prefix(t, class_id)
    t = strip_generic_leading_label(t)
    print('after prefix/label ->', repr(t))
    tokens = t.split()
    print('tokens ->', tokens)
    kept = []
    stop_words = {"name", "full", "father", "mother", "gender", "sex", "dob", "date",
                  "neme", "nemes", "fuh", "ful", "fulll", 
                  "namae", "nams", "nam", "nem", "it",     
                  "of", "oy", "ofs", "oys", "s", "नामथर"}
    for tok in tokens:
        low = tok.lower()
        if low in stop_words:
            print('drop stop_word', tok)
            continue
        if __import__('re').fullmatch(r"[A-Za-z\u0900-\u097F'’\-]+", tok):
            print('allow token', tok)
            kept.append(tok)
        else:
            print('reject token by pattern', tok)
    print('kept ->', kept)

if __name__ == '__main__':
    print('DEBUG Father Name:')
    debug('Father Name: Ram Kumar', 2)
    print('\nDEBUG Mother Name:')
    debug('Mother Name: Sita Devi', 3)
    print('\nDEBUG Ram Kumar (plain):')
    debug('Ram Kumar', 2)
    print('\nDEBUG reported Nepali cases:')
    debug('धरः भरत बहादुर शाह', 2)
    debug('उअकैको नाम लक्ष्मी कुमारी सिंह', 3)
