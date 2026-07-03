from main import clean_field_text

# Test various ward number formats
test_cases = [
    ("Ward No.:i8", 12, "18"),
    ("Ward No. 15", 12, "15"),
    ("Ward Nowi8", 12, "18"),
    ("Ward No.18", 12, "18"),
    ("WARD NO: 05", 12, "5"),
    ("Ward 35", 12, "35"),
    ("Ward", 12, ""),  # Just label, no number
    ("वर्ड नं 12", 12, "12"),  # Nepali: Ward No 12
    ("वर्ड नंबर २०", 12, "20"),  # Nepali with Nepali digits
    ("Ward 0", 12, ""),  # Zero is invalid
    ("Ward 100", 12, "100"),  # 3-digit ward (extended range)
    ("Ward -5", 12, "5"),  # Negative sign removed
    ("Ward No.:i8", 12, "18"),  # OCR "i" misread
    ("", 12, ""),  # Empty
]

print("Ward Number Extraction Tests:")
print("=" * 70)
passed = 0
failed = 0

for input_text, class_id, expected in test_cases:
    result = clean_field_text(input_text, class_id)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    if result == expected:
        passed += 1
    else:
        failed += 1
    print(f"{status} | '{input_text}' → '{result}' (expected: '{expected}')")

print("=" * 70)
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("All ward extraction tests passed!")
