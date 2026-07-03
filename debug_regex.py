import re

text = 'i8'
print(f"Testing: {repr(text)}")
print(f"Character codes: {[hex(ord(c)) for c in text]}")

# Test the regex
pattern = r'^[Il]+'
print(f"Pattern: {pattern}")
print(f"RE.match result: {re.match(pattern, text)}")
print(f"RE.search result: {re.search(pattern, text)}")

# Try with lambda
result = re.sub(r'^[Il]+', lambda m: '1' * len(m.group()), text)
print(f"After sub: {repr(result)}")

# What about just 'i'?
result2 = re.sub(r'^i', '1', text)
print(f"After simple i→1: {repr(result2)}")

# Maybe the issue is the regex is not matching?
match = re.match(r'^[Il]+', text)
print(f"Match object: {match}")
if match:
    print(f"Matched: {repr(match.group())}")
