from main import normalize_ocr_text, nepali_to_english_digits

cases = [
    ("Name:\nASHIKA  SHARMA  ", normalize_ocr_text),
    ("१२३४५६७८९", nepali_to_english_digits),
    ("12O34", nepali_to_english_digits),
    ("1|234", nepali_to_english_digits),
    ("\n\x0cHello — World!!\t", normalize_ocr_text),
]

for inp, fn in cases:
    print(f"INPUT: {repr(inp)} -> {fn.__name__}: {fn(inp)}")
