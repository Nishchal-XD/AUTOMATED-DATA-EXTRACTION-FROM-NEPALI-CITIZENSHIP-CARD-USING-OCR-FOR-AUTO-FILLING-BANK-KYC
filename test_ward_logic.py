import sys
import re

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[©®™•·]", "", text)
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

def strip_field_prefix(text, class_id):
    FIELD_PREFIX_PATTERNS = {
        12: [r"ward\s*(?:no(?:w|\.)?|number)", r"(?:वर्ड|वर्ड)\s*(?:नं|नंबर|न०)"],
    }
    patterns = FIELD_PREFIX_PATTERNS.get(class_id, [])
    for base in patterns:
        text = re.sub(
            rf"(?i)^\s*{base}\s*[:./\-–—_]*\s*",
            "",
            text,
            count=1
        )
    return text

def clean_ward_number(text):
    """Test version of ward cleaning"""
    print(f"\n→ Step 1: Input: '{text}'")
    
    text = normalize_ocr_text(text)
    print(f"→ Step 2 (normalize): '{text}'")
    
    if ":" in text or ";" in text:
        text = re.split(r"[:;]", text)[-1].strip()
        print(f"→ Step 3 (split by colon): '{text}'")
    
    text = strip_field_prefix(text, 12)
    print(f"→ Step 4 (strip prefix): '{text}'")
    
    text = nepali_to_english_digits(text)
    print(f"→ Step 5 (nepali_to_english): '{text}'")
    
    digits_only = re.sub(r"[^\d]", "", text).strip()
    print(f"→ Step 6 (extract digits): '{digits_only}'")
    
    if digits_only:
        try:
            ward_val = int(digits_only)
            if 1 <= ward_val <= 999:
                print(f"→ Step 7 (validate): Valid ward number = {ward_val}")
                return str(ward_val)
        except:
            pass
    
    print(f"→ Step 7 (validate): Invalid/Empty → returning ''")
    return ""

# Test cases
test_cases = [
    "Ward No.:i8",
    "Ward No.18",
    "4",
    "Ward No.: 12",
    "",
    "Ward 35",
    "वर्ड नं 12",
]

for test in test_cases:
    print("=" * 60)
    result = clean_ward_number(test)
    print(f"  FINAL RESULT: '{result}'")
