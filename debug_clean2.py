import re

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[©®™•·]", "", text)
    return text

FIELD_PREFIX_PATTERNS = {
    2: [
        r"(?:father\s*'?s?)\s*name",
        r"(?:बुव(?:ाको|ुको)?|बाबु(?:को)?|बुब)(?:को)?(?:\s*नर/?थेर)?",
        r"बुबुको\s*नर/?थेर"
    ],
}

def strip_field_prefix(text, class_id):
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


def clean_field_text_test(text, class_id):
    print('original', text)
    text = normalize_ocr_text(text)
    print('normalized', text)
    text = strip_field_prefix(text, class_id)
    print('after strip_prefix', text)
    text = strip_generic_leading_label(text)
    print('after generic_label', text)
    text = re.sub(r"^\W+|\W+$", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"\s+", " ", text).strip()
    print('after trim', text)
    if class_id in {1,2,3,5}:
        tokens=text.split(); kept=[]
        stop_words={"name","full","father","mother","gender","sex","dob","date"}
        for tok in tokens:
            low=tok.lower()
            if low in stop_words: continue
            if re.fullmatch(r"[A-Za-z\u0900-\u097F'’\-]+", tok):
                kept.append(tok)
        text=" ".join(kept)
        print('after token_filter', text)
    for i in range(2):
        if ":" in text or ";" in text:
            print('colon loop',i,'before',text)
            text = re.split(r"[:;]", text)[-1].strip()
            text = re.sub(r"^\W+|\W+$", "", text, flags=re.UNICODE).strip()
            print('after split', text)
            if class_id in {1,2,3,5}:
                text = strip_field_prefix(text, class_id)
                text = strip_generic_leading_label(text)
                print('after prefix/generic in loop',text)
    return text

print('result:', clean_field_text_test('बुबुको नर/थेर: महेश निरौल',2))
