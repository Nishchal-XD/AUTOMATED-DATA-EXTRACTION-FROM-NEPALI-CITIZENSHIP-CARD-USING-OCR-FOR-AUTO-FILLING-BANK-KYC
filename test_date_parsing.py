from main import parse_to_html_date

test_cases = [
    ("जारी मिति : २०५२९.०७-०२", "2052-09-02"),  # 5-digit year: 20529 => 2052-9
    ("Issued Date: 2019/7/4", "2019-07-04"),  # English
    ("Date: 2076-04-12", "2076-04-12"),
    ("2076-04-12", "2076-04-12"),
    ("04-12-2076", "2076-12-04"),  # DD-MM-YYYY interpretation (day=04, month=12, year=2076)
    ("जारी मिति : २०७६-०४-१२", "2076-04-12"),  # Nepali digits
    ("", ""),  # Empty
]

print("Date Parsing Tests:")
print("=" * 60)
passed = 0
failed = 0

for input_text, expected in test_cases:
    result = parse_to_html_date(input_text)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    if result == expected:
        passed += 1
    else:
        failed += 1
    print(f"{status} | '{input_text}' -> '{result}' (expected: '{expected}')")

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("All tests passed!")
