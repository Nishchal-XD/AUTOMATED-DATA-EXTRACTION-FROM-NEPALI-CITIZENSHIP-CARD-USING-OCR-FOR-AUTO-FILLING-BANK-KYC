import re

text = 'i8'
print(f"Testing: {repr(text)}")

# Test the character class
patterns = [
    r'^[iI]',     # lowercase i and uppercase I
    r'^[lL]',     # lowercase l and uppercase L
    r'^[ilIL]',   # all four
    r'^[Il]',     # the original that didn't work
]

for pattern in patterns:
    match = re.match(pattern, text)
    print(f"Pattern {repr(pattern):20} → Match: {match is not None}")
    if match:
        print(f"    Matched: {repr(match.group())}")

# Check actual character codes
print(f"\nCharacter codes in '[Il]':")
for c in "[Il]":
    print(f"  {c} → {hex(ord(c))}")

# Try to use the wrong one and see what happens
text2 = 'I8'
match2 = re.match(r'^[Il]', text2)
print(f"\n'I8' with ^[Il]: {match2}")
