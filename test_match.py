import difflib
import re

def nepali_to_roman(text):
    if not text:
        return ""
    mapping = {
        'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
        'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
        'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
        'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
        'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
        'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh',
        'ष': 'sh', 'स': 's', 'ह': 'h', 'क्ष': 'ksh', 'त्र': 'tr', 'ज्ञ': 'gy',
        'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
        'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', 'ः': 'h',
        'अ': 'a', 'आ': 'a', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
        '्': ''
    }
    result = ""
    for char in text:
        result += mapping.get(char, char)
    return result.lower()

front = "शुवम पन्थ"
back = "SUBAM PANTHA"

romanized_front = nepali_to_roman(front)

rf_clean = re.sub(r'[^a-z]', '', romanized_front.lower())
bn_clean = re.sub(r'[^a-z]', '', back.lower())

similarity = difflib.SequenceMatcher(None, rf_clean, bn_clean).ratio()
print(f"rf_clean: {rf_clean}, bn_clean: {bn_clean}, similarity: {similarity}")

# Testing what happens in cross_correct_nepali_name
nep_tokens = front.split()
eng_tokens = [t.lower() for t in back.split()]

print(f"nep_tokens: {nep_tokens}")
print(f"eng_tokens: {eng_tokens}")

for i, nep_tok in enumerate(nep_tokens):
    romanised = nepali_to_roman(nep_tok)
    matches = difflib.get_close_matches(romanised, eng_tokens, n=1, cutoff=0.55)
    print(f"tok: {nep_tok}, romanised: {romanised}, matches: {matches}")
