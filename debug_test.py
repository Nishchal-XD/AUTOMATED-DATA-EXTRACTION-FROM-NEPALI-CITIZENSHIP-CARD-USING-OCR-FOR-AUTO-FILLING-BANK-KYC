import sys
sys.path.append(r"c:\nagarikta")
from main import clean_field_text

examples = [
    ('Full Name; John Doe', 1),
    ('father name: Ram', 2),
    ('Mother Name; Sita', 3),
    ('full name ;', 1),
    ('नाम थर; सरिष्मा न्यौपान', 1),
    ('full name;  ', 1),
]
for text, cid in examples:
    print(f"'{text}' -> '{clean_field_text(text, cid)}'")
