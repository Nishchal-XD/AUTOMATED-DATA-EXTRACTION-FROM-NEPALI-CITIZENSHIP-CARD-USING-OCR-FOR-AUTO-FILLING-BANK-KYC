"""Test ward number extraction from main.py logic"""
import re

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text

def nepali_to_english_digits(text):
    """Convert Nepali digits to English digits and fix common OCR misreads"""
    if not text:
        return ""
    
    # Convert Nepali digits to English
    nep = "०१२३४५६७८९"
    eng = "0123456789"
    table = str.maketrans(nep, eng)
    text = text.translate(table)
    
    # Fix common OCR mistakes: letters i,I,l,L misread as '1' and O,o as '0'
    # Handle leading i/I/l/L which are often OCR errors for '1'
    text = re.sub(r'^[ilIL]+', lambda m: '1' * len(m.group()), text)
    
    # Replace combinations of i/I/l/L with '1' for each character
    text = re.sub(r'[ilIL][ilIL]', lambda m: '1' * len(m.group()), text)
    # Replace standalone i/I/l/L between digits with '1'
    text = re.sub(r'(\d)[ilIL](?=\d)', r'\g<1>1', text)
    text = re.sub(r'(?<=\d)[ilIL](\d)', r'1\g<1>', text)
    # Replace 'O' or 'o' surrounded by digits with '0'
    text = re.sub(r'(\d)[Oo](?=\d)', r'\g<1>0', text)
    text = re.sub(r'(?<=\d)[Oo](\d)', r'0\g<1>', text)
    
    return text

FIELD_PREFIX_PATTERNS = {
    12: [r"ward\s*(?:no(?:w|\.)?|number)"],  # Handles 'wardno', 'wardno.', 'wardnow' variants
}

def strip_field_prefix(text, class_id):
    patterns = FIELD_PREFIX_PATTERNS.get(class_id, [])
    for base in patterns:
        text = re.sub(
            rf"(?i)^\s*{base}\s*[:.\-–—_]*\s*",
            "",
            text,
            count=1
        )
    return text

def clean_field_text_ward(text, class_id):
    """Clean OCR text for ward number (class_id 12)"""
    text = normalize_ocr_text(text)
    
    if class_id == 12:  # Ward number - extract numbers and validate
        text = strip_field_prefix(text, class_id)
        text = nepali_to_english_digits(text)
        text = re.sub(r"[^\d]", "", text).strip()
        # Validate ward number is 1-99
        if text:
            try:
                ward_val = int(text)
                if 1 <= ward_val <= 99:
                    return str(ward_val)
            except:
                pass
        return text
    
    return text

# Test cases with real OCR samples from cache
test_cases = [
    ("Ward No.:i8", "18"),
    ("Ward No. 12", "12"),
    ("Ward Nowi8", "18"),
    ("Ward No.18", "18"),
    ("WARD NO: 05", "5"),  # Should return "5" (valid 1-99)
    ("Ward 35", "35"),
]

print("Testing Ward Number Extraction:")
print("=" * 70)

all_passed = True
for raw_text, expected in test_cases:
    result = clean_field_text_ward(raw_text, 12)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    if result != expected:
        all_passed = False
    print(f"{status} | '{raw_text}' → '{result}' (expected: '{expected}')")

print("=" * 70)
print(f"Overall: {'All tests passed!' if all_passed else 'Some tests failed'}")
