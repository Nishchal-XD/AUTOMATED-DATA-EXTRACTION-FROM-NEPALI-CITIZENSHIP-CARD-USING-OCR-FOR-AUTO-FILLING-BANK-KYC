#!/usr/bin/env python3
"""
Comprehensive test for Permanent Address Field Extraction
Tests extraction of: perm_district, perm_address, perm_ward_no
"""
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
    """Clean permanent district field"""
    text = normalize_ocr_text(text)
    text = re.sub(r"(?i)^.*?district\s*[:=]*\s*", "", text).strip()
    text = re.sub(r"[^A-Za-z\s]", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_perm_address(text):
    """Clean permanent address field"""
    text = normalize_ocr_text(text)
    text = re.sub(r"(?i)^permanent\s*address\s*[:\-–—.]*\s*", "", text).strip()
    text = re.sub(r"(?i)^(?:metropolitan|metro)\s*[:\-–—.]*\s*", "", text).strip()
    text = re.sub(r"(?i)\s*[–—-]?\s*(?:district|dist)\s*[:=]*\s*.*$", "", text).strip()
    text = re.sub(r"[,._\-–—]+", " ", text).strip()
    text = re.sub(r"^[^\w]+|[^\w]+$", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Test cases
test_cases = [
    (10, "Permanent Address:.-. — District: LALITPUR", "perm_district", "LALITPUR"),
    (11, "Metropolitan : Lalitpur", "perm_address", "Lalitpur"),
    (12, "Ward No.:i8", "perm_ward_no", "18"),
    # Additional test cases
    (10, "District: KATHMANDU", "perm_district", "KATHMANDU"),
    (11, "Permanent Address: Thamel, Kathmandu", "perm_address", "Thamel Kathmandu"),
    (12, "Ward No. 15", "perm_ward_no", "15"),
]

print("\n" + "=" * 80)
print("PERMANENT ADDRESS FIELD EXTRACTION TEST")
print("=" * 80)

passed = 0
failed = 0

for class_id, raw_text, field_name, expected in test_cases:
    if class_id == 10:
        result = clean_perm_district(raw_text)
    elif class_id == 11:
        result = clean_perm_address(raw_text)
    elif class_id == 12:
        text = normalize_ocr_text(raw_text)
        text = re.sub(r"(?i)^\s*ward\s*(?:no|number)\s*[:.\-–—_]*\s*", "", text, count=1)
        text = nepali_to_english_digits(text)
        result = re.sub(r"[^\d]", "", text).strip()
    
    is_pass = result == expected
    status = "✓ PASS" if is_pass else "✗ FAIL"
    if is_pass:
        passed += 1
    else:
        failed += 1
    
    print(f"\n{status} | {field_name:20}")
    print(f"       Input:    '{raw_text}'")
    print(f"       Got:      '{result}'")
    print(f"       Expected: '{expected}'")

print("\n" + "=" * 80)
print(f"RESULTS: {passed} PASSED, {failed} FAILED (Total: {passed + failed})")
print("=" * 80 + "\n")

if failed == 0:
    print("✓ All permanent address field extraction tests PASSED!")
else:
    print(f"✗ {failed} test(s) FAILED. Please review the output above.")
