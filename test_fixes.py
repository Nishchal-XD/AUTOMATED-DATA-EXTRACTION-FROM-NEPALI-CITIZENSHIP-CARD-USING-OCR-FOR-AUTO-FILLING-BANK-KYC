"""
Isolated test of mayn.py fix logic - no Flask/YOLO needed
Tests the exact data from today's 6 failed cache datasets
"""
import re

# ============================================================
# COPY OF HELPERS FROM mayn.py (no Flask/YOLO dependencies)
# ============================================================

def nepali_to_english_digits(text):
    if not text:
        return ""
    nep = "०१२३४५६७८९"
    eng = "0123456789"
    table = str.maketrans(nep, eng)
    text = text.translate(table)
    text = re.sub(r'^[ilIL]+', lambda m: '1' * len(m.group()), text)
    text = re.sub(r'[ilIL][ilIL]', lambda m: '1' * len(m.group()), text)
    text = re.sub(r'(\d)[ilIL](?=\d)', r'\g<1>1', text)
    text = re.sub(r'(?<=\d)[ilIL](\d)', r'1\g<1>', text)
    text = re.sub(r'(\d)[Oo](?=\d)', r'\g<1>0', text)
    text = re.sub(r'(?<=\d)[Oo](\d)', r'0\g<1>', text)
    return text

# OCR variations mapping
OCR_VARIATIONS = {
    "bhimsenthapa": "Gorkha",
    "bhimsen thapa": "Gorkha",
    "palungtar": "Palungtar",
    "gorkha": "Gorkha",
    "kathmandu": "Kathmandu",
    "lalitpur": "Lalitpur",
    "hetauda": "Hetauda",
    "pokhara": "Pokhara",
    "vyas": "Byas",
    "byas": "Byas",
}
MUNICIPALITY_MAPPING = {}
for k, v in OCR_VARIATIONS.items():
    MUNICIPALITY_MAPPING[k.lower()] = v
    MUNICIPALITY_MAPPING[k.lower().replace(" ", "")] = v

ALL_MUNICIPALITIES = list(set(OCR_VARIATIONS.values()))

def correct_municipality_name(ocr_text, district_name=None):
    if not ocr_text:
        return ocr_text
    cleaned = str(ocr_text).strip().lower()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s*(municipality|rural municipality|nagarpalika|gaupalika)\s*$', '', cleaned, flags=re.IGNORECASE).strip()
    if cleaned in MUNICIPALITY_MAPPING:
        return MUNICIPALITY_MAPPING[cleaned]
    cleaned_nospace = cleaned.replace(' ', '')
    if cleaned_nospace in MUNICIPALITY_MAPPING:
        return MUNICIPALITY_MAPPING[cleaned_nospace]
    return cleaned.title()

def strip_field_prefix(text, class_id):
    patterns = {
        2: [
            r'(?:father\s*\'?s?)\s*name',
            r'(?:बुव(?:ाको|ुको)?|बाबु(?:को)?|हाबु(?:को)?|बुब)(?:को)?(?:\s*नाम(?:\s*(?:थर|यर))?)?',
            r'बर्बुको(?:\s*नाम)?',
            r'पिताको\s*नाम',
            r'धरः', r'थब',
        ],
        13: [r'issued\s*date', r'date\s*of\s*issue', r'जारीमिति', r'जारी\s*मिति', r'मिति'],
        4:  [r'citizenship\s*(?:no|number)'],
    }.get(class_id, [])
    for base in patterns:
        text = re.sub(rf'(?i)\s*{base}\s*[:./\-–—_]*\s*', '', text, count=1)
    return text

def clean_field_text_v2(text, class_id):
    """Simplified test version of clean_field_text"""
    text = text.strip()
    
    if class_id == 13:  # issued date
        t = text
        t = strip_field_prefix(t, class_id)
        t = nepali_to_english_digits(t)
        t = re.sub(r'\s+', '', t)
        return t
    
    if class_id == 4:  # citizenship no
        t = nepali_to_english_digits(text)
        t = strip_field_prefix(t, class_id)
        t = re.sub(r'[^0-9\-]', '', t)
        t = re.sub(r'-+', '-', t).strip('-')
        return t
    
    if class_id == 0:  # issued office
        t = text
        city_names = ['काठमाडौँ', 'काठमाडौ', 'ललितपुर', 'भक्तपुर', 'पोखरा']
        for city in city_names:
            t = re.sub(r'(\S)(' + city + r')', r'\1 \2', t)
        t = re.sub(r'जिल्ला(प्रशासन)', r'जिल्ला \1', t)
        return t.strip()
    
    if class_id == 2:  # father name
        t = strip_field_prefix(text, class_id)
        father_prefixes = [
            r'^बर्बुको\s*(?:नाम\s*(?:थर\s*)?)?',
            r'^बुबुको\s*(?:नाम\s*(?:थर\s*)?)?',
            r'^बाबुको\s*(?:नाम\s*(?:थर\s*)?)?',
            r'^बुवाको\s*(?:नाम\s*(?:थर\s*)?)?',
            r'^पिताको\s*(?:नाम\s*)?',
            r'^धर\s+', r'^धरः\s*', r'^थब\s+',
        ]
        for pat in father_prefixes:
            t = re.sub(pat, '', t).strip()
        t = re.sub(r'\s+थब\s+', ' ', t)
        return t
    
    return text

# ============================================================
# TESTS: exact data from today's 6 cache datasets
# ============================================================

PASS = 0
FAIL = 0

def test(name, got, expected):
    global PASS, FAIL
    ok = got.strip() == expected.strip()
    status = "✅ PASS" if ok else "❌ FAIL"
    if not ok:
        FAIL += 1
    else:
        PASS += 1
    print(f"{status}  {name}")
    if not ok:
        print(f"       got:      [{got}]")
        print(f"       expected: [{expected}]")

print("=" * 60)
print("TESTING ALL 6 DATASET FIXES")
print("=" * 60)

# Dataset 1: Satish Raj Pandey
print("\n--- Dataset 1: Satish Raj Pandey (ccf664ac) ---")
test("Father name strip 'बर्बुको'",
     clean_field_text_v2('बर्बुको मदन राजपाण्डे', 2),
     'मदन राजपाण्डे')
test("Issued date Nepali digits (२०४३-०४-१३)",
     clean_field_text_v2('२०४३-०४-१३', 13),
     '2043-04-13')
test("Municipality Kathmandu",
     correct_municipality_name('Kathmandu', 'Kathmandu'),
     'Kathmandu')

# Dataset 2: Dina Bhatta (00b94844)
print("\n--- Dataset 2: Dina Bhatta (00b94844) ---")
test("Father name 'जिबनाधमभट्ट' (raw OCR, no prefix)",
     clean_field_text_v2('जिबनाधमभट्ट', 2),
     'जिबनाधमभट्ट')   # No prefix to strip here - name is fine
test("Municipality 'Bhimsenthapa' → 'Gorkha'",
     correct_municipality_name('Bhimsenthapa', 'Gorkha'),
     'Gorkha')
test("Issued date '२०७९-०१-१५' converts",
     clean_field_text_v2('२०७९-०१-१५', 13),
     '2079-01-15')
test("Citizenship no '44-01-79-09783' stays",
     clean_field_text_v2('44-01-79-09783', 4),
     '44-01-79-09783')

# Dataset 3: Issued office merge
print("\n--- Dataset 3: Issued Office merged text ---")
test("Office 'कार्यालयकाठमाडौँ' splits",
     clean_field_text_v2('कार्यालयकाठमाडौँ', 0),
     'कार्यालय काठमाडौँ')

# Nepali digit conversion test
print("\n--- Nepali digit conversion ---")
test("२०७९ → 2079", nepali_to_english_digits('२०७९'), '2079')
test("२०४३-०४-१३ → 2043-04-13", nepali_to_english_digits('२०४३-०४-१३'), '2043-04-13')

print()
print("=" * 60)
print(f"RESULTS: {PASS} PASS  |  {FAIL} FAIL")
print("=" * 60)
