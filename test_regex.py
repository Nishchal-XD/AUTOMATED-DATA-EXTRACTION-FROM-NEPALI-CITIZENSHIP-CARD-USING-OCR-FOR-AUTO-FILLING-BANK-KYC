import re

text = 'i8'
print(f"Testing: {repr(text)}")

# Test individual patterns
patterns = [
    r'^i',
    r'^I',
    r'^l',
    r'^L',
    r'^[i]',
    r'^[I]',
    r'^[Il]',
    r'^[iI]',
]

for pattern in patterns:
    match = re.match(pattern, text)
    print(f"Pattern {repr(pattern):20} → {match is not None}")
