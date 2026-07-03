import re

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text

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

def clean_perm_district(text):
    text = normalize_ocr_text(text)
    text = re.sub(r"(?i)^.*?district\s*[:=]*\s*", "", text).strip()
    text = re.sub(r"[^A-Za-z\s]", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_perm_address(text):
    text = normalize_ocr_text(text)
    text = re.sub(r"(?i)^permanent\s*address\s*[:\-–—.]*\s*", "", text).strip()
    text = re.sub(r"(?i)^(?:metropolitan|metro)\s*[:\-–—.]*\s*", "", text).strip()
    text = re.sub(r"(?i)\s*[–—-]?\s*(?:district|dist)\s*[:=]*\s*.*$", "", text).strip()
    text = re.sub(r"^[^\w]+|[^\w]+$", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text

test_cases = [
    (10, "Permanent Address:.-. — District: LALITPUR", "LALITPUR"),
    (11, "Metropolitan : Lalitpur", "Lalitpur"),
    (12, "Ward No.:i8", "18"),
]

print("Testing Permanent Address Fields Extraction:")
print("=" * 70)
for class_id, raw_text, expected in test_cases:
    if class_id == 10:
        result = clean_perm_district(raw_text)
    elif class_id == 11:
        result = clean_perm_address(raw_text)
    elif class_id == 12:
        text = nepali_to_english_digits(raw_text.replace("Ward No.:", ""))
        result = re.sub(r"[^\d]", "", text).strip()
    
    status = "✓ PASS" if result == expected else "✗ FAIL"
    field_name = {10: "perm_district", 11: "perm_address", 12: "perm_ward_no"}.get(class_id, "unknown")
    print(f"{status} | {field_name:20} | '{raw_text}' → '{result}' (expected: '{expected}')")
print("=" * 70)
