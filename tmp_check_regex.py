import re

text1 = 'दीनेश सुनार'
text2 = 'कामी'

def clean(t):
    return re.sub(r"^\W+|\W+$", "", t, flags=re.UNICODE).strip()

print(f"Original: '{text1}' -> Cleaned: '{clean(text1)}'")
print(f"Original: '{text2}' -> Cleaned: '{clean(text2)}'")
