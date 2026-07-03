from main import clean_field_text

# Test the problematic extractions
test_cases = [
    # Full name issue: "Fuh Nemes" suggests OCR garbled the label
    ("Fuh Nemes ROJEN MAHARJAN", 5, "ROJEN MAHARJAN"),
    ("Full Name.: ROJEN MAHARJAN", 5, "ROJEN MAHARJAN"),
    ("Full Nemes ROJEN MAHARJAN", 5, "ROJEN MAHARJAN"),
    
    # Mother name issue: includes "धरः" (tar:) in output
    ("धरः करुणा महर्जन", 3, "करुणा महर्जन"),
    ("आमाको नाम धरः करुणा महर्जन", 3, "करुणा महर्जन"),
    
    # DOB components - need to see why they're blank
    ("Year-2003", 7, "2003"),
    ("Month-JUL", 8, "07"),
    ("Day-15", 9, "15"),
    ("", 7, ""),
    ("", 8, ""),
    ("", 9, ""),
]

print("Case-by-case cleaning test:")
print("=" * 80)

for raw_text, class_id, expected in test_cases:
    result = clean_field_text(raw_text, class_id)
    status = "✓" if result == expected else "✗"
    label = {3:'mother', 5:'fullname', 7:'year', 8:'month', 9:'day'}.get(class_id, f'class_{class_id}')
    print(f"{status} [{label:8s}] '{raw_text[:40]:40s}' → '{result}'")
    if result != expected:
        print(f"           Expected: '{expected}'")
