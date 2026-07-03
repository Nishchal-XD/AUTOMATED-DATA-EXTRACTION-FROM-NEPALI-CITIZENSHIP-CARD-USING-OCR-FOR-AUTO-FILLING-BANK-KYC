import sys
sys.path.append(r"c:\nagarikta")
from main import parse_to_html_date, clean_field_text

cases = [
    ("जारी मिति : २०७६-०४-१२", "2076-04-12", "Nepali issued date should parse"),
    ("Issued Date: 2019/7/4", "2019-07-04", "English date with slashes"),
    ("Issue Date: 27-0!-71-04696", "", "No valid date, should return empty"),
]

print("Testing issued date parsing:")
print("="*60)
all_good = True
for raw, expected, desc in cases:
    got = parse_to_html_date(raw)
    ok = got == expected
    print(("✓" if ok else "✗"), desc, "->", repr(got), "(expected:", repr(expected)+")")
    if not ok:
        all_good = False

# document number cleaning (class_id 4)
print("\nTesting document/citizenship cleaning:")
print("="*60)
doc_cases = [
    ("27-0!-71-04696", "27-0-71-04696"),
    ("Citizenship Certificate No.: . 28-01-76-02213.", "28-01-76-02213"),
    ("०२८-०१-७६-०२२१३", "028-01-76-02213"),
]
for raw, expected in doc_cases:
    got = clean_field_text(raw, 4)
    ok = got == expected
    print(("✓" if ok else "✗"), raw, "->", repr(got), "(expected:", repr(expected)+")")
    if not ok:
        all_good = False

print("\nAll good:" if all_good else "Some tests failed")
