import sys
import re
sys.path.append(r"c:\nagarikta")
from main import clean_perm_district, clean_perm_address, nepali_to_english_digits

test_cases = [
    (10, "Permanent Address:.-. — District: LALITPUR", "LALITPUR"),
    (11, "Metropolitan : Lalitpur", "Lalitpur"),
    (12, "Ward No.:i8", "18"),
    # cases where the naive clean strips everything should fall back to raw content
    (11, "Permanent Address: XYZ 123", "XYZ 123"),
    (10, "District:/", ""),  # nothing to return even fallback
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
        if result:
            try:
                ward_val = int(result)
                if 1 <= ward_val <= 99:
                    result = str(ward_val)
            except:
                pass
    
    status = "✓ PASS" if result == expected else "✗ FAIL"
    field_name = {10: "perm_district", 11: "perm_address", 12: "perm_ward_no"}.get(class_id, "unknown")
    print(f"{status} | {field_name:20} | '{raw_text}' → '{result}' (expected: '{expected}')")
print("=" * 70)
