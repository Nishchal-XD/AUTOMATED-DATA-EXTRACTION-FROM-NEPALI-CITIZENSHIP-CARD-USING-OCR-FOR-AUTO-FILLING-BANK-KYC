from main import clean_field_text

# Test with actual values from cache
test_cases = [
    ("Ward No.:i8", 12),
    ("Ward No.18", 12),
    ("4", 12),
    ("Ward No.: 12", 12),
    ("", 12),
]

print("Testing clean_field_text for ward numbers:")
for text, class_id in test_cases:
    result = clean_field_text(text, class_id)
    print(f"Input: '{text}' → Output: '{result}'")
