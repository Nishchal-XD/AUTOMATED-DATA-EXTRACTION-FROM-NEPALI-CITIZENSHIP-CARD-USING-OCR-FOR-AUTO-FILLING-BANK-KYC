import re

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[©®™•·]", "", text)
    return text

def strip_field_prefix(text, class_id):
    FIELD_PREFIX_PATTERNS = {
        0: [r"issued\s*office", r"office"],
        1: [r"name", r"full\s*name"],
        2: [r"(?:father\s*'?s?)\s*name", r"(?:बुव(?:ाको|ुको)?|बाबु(?:को)?|बुब)"],
        3: [r"(?:mother\s*'?s?)\s*name", r"(?:आम).{0,20}(?=:)"]
    }
    patterns = FIELD_PREFIX_PATTERNS.get(class_id, [])
    for base in patterns:
        text = re.sub(
            rf"(?i)^\s*{base}\s*[:./\-–—_]*\s*",
            "",
            text,
            count=1
        )
    return text

def strip_generic_leading_label(text):
    match = re.match(
        r"^\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{1,40})\s*[:;._\-–—_\"'“”?]+\s*(.+)$",
        text,
    )
    if match:
        return match.group(2).strip()
    return text

def clean_field_text(text, class_id):
    original = text
    text = normalize_ocr_text(text)
    text = strip_field_prefix(text, class_id)
    text = strip_generic_leading_label(text)
    text = re.sub(r"^\W+|\W+$", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"\s+", " ", text).strip()
    print("after initial strip:", repr(text))
    if class_id in {1,2,3,5}:
        tokens = text.split()
        kept=[]
        stop_words={"name","full","father","mother","gender","sex","dob","date"}
        for tok in tokens:
            low=tok.lower()
            if low in stop_words:
                print("dropping stop word token", tok)
                continue
            if re.fullmatch(r"[A-Za-z\u0900-\u097F'’\-]+", tok):
                if re.search(r"[A-Z][a-z].*[A-Z]", tok):
                    print("dropping mixed-case token", tok)
                    continue
                if len(tok)==1 and not re.match(r"[\u0900-\u097F]", tok) and len(tokens)>1:
                    print("dropping one-letter token", tok)
                    continue
                kept.append(tok)
            else:
                print("token didn't match pattern", tok)
        text=" ".join(kept)
        print("after token filter:", repr(text))
    for i in range(2):
        if ":" in text or ";" in text:
            print("colon loop iteration", i, "text before split", repr(text))
            text = re.split(r"[:;]", text)[-1].strip()
            text = re.sub(r"^\W+|\W+$", "", text, flags=re.UNICODE).strip()
            print("after split", repr(text))
            if class_id in {1,2,3,5}:
                text = strip_field_prefix(text, class_id)
                text = strip_generic_leading_label(text)
                print("after prefix/generic in loop", repr(text))
    return text

print(clean_field_text("Full name; father name: Ram Kumar", 2))
print(clean_field_text("Full Name;", 5))
print(clean_field_text("Full Name;  ", 5))
