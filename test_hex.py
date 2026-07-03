import re

# Test by checking the actual hex codes in the pattern
pattern = r'^[Il]'
print(f"Pattern: {repr(pattern)}")
print(f"Pattern hex codes: {[hex(ord(c)) for c in pattern]}")

text = 'i8'
print(f"Text: {repr(text)}")  
print(f"Text hex codes: {[hex(ord(c)) for c in text]}")

match = re.match(pattern, text)
print(f"Match result: {match}")

# Try with explicit lowercase l
pattern2 = r'^[i' + chr(0x6c) + ']'
print(f"\nPattern2 (with chr(0x6c)): {repr(pattern2)}")
print(f"Pattern2 hex codes: {[hex(ord(c)) for c in pattern2]}")
match2 = re.match(pattern2, text)
print(f"Match2 result: {match2}")

# Use iI and l separately
pattern3 = r'^[iIl]'
print(f"\nPattern3: {repr(pattern3)}")
print(f"Pattern3 hex codes: {[hex(ord(c)) for c in pattern3]}")
match3 = re.match(pattern3, text)
print(f"Match3 result: {match3}")
