import re
import unicodedata

# Class mapping to languages
placeholder = {
    0: "nep", 1: "nep", 2: "nep", 3: "nep",
    4: "eng", 5: "eng", 6: "eng", 7: "eng",
    8: "eng", 9: "eng", 10: "eng", 11: "eng",
    12: "eng", 13: "nep"
}

# dictionary for manual name corrections (lowercase keys)
NAME_CORRECTIONS = {
    "aasisa shrestha": "aashish shrestha",
}


def nepali_to_english_digits(text):
    """Convert Nepali digits to English digits and fix common OCR misreads"""
    if not text:
        return ""
    nep = "०१२३४५६७८९"
    eng = "0123456789"
    table = str.maketrans(nep, eng)
    text = text.translate(table)
    # Also convert Arabic-Indic digits
    arab = "٠١٢٣٤٥٦٧٨٩"
    text = text.translate(str.maketrans(arab, eng))
    text = unicodedata.normalize('NFKC', text)
    text = text.strip()
    # fix OCR mistakes
    text = re.sub(r'^[ilIL\|!]+', lambda m: '1' * len(m.group()), text)
    text = re.sub(r'([ilIL]{2,})', lambda m: '1' * len(m.group()), text)
    text = re.sub(r'(\d)[ilIL](?=\d)', r'\g<1>1', text)
    text = re.sub(r'(?<=\d)[ilIL](\d)', r'1\g<1>', text)
    text = re.sub(r'(\d)[Oo](?=\d)', r'\g<1>0', text)
    text = re.sub(r'(?<=\d)[Oo](\d)', r'0\g<1>', text)
    return text


def normalize_ocr_text(text):
    if not text:
        return ""
    # Unicode normalize to collapse compatibility characters
    text = unicodedata.normalize('NFKC', str(text))
    # remove control chars and collapse line breaks to spaces
    text = text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').replace('\x0c', ' ')
    # replace various smart quotes and guillemets with a simple apostrophe
    text = re.sub(r"[“”«»„`´‘’]", "'", text)
    # remove common stray symbols that routinely show up in OCR output
    text = re.sub(r"[©®™•·•]", "", text)

    # Fix common OCR homoglyphs in digit contexts: pipes/exclamation/ellipses misread as 1, O as 0
    text = re.sub(r'(?<=\d)[ilI\|!]+(?=\d)', '1', text)
    text = re.sub(r'(?<=\d)[Oo]+(?=\d)', '0', text)

    # Replace standalone vertical bars or pipes that are likely noise
    text = re.sub(r'[\|]{2,}', '|', text)

    # Remove any zero-width / non-printable characters
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')

    # Collapse multiple whitespace and trim
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_perm_district(text):
    """Clean permanent district field"""
    text = normalize_ocr_text(text)
    # Remove all labels and special characters first - keep what's after "District:"
    # Match "District:" and capture what comes after, handle multiple occurrences
    text = re.sub(r"(?i).*?district\s*[:=]*\s*", "", text).strip()
    # Also handle cases where label might not have been removed
    text = re.sub(r"(?i)^[^a-z]*", "", text).strip()
    # Keep only letters and spaces
    text = re.sub(r"[^A-Za-z\s]", "", text).strip()
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_perm_address(text):
    """Clean permanent address field"""
    text = normalize_ocr_text(text)
    # Remove permanent address labels
    text = re.sub(r"(?i)^permanent\s*address\s*[:\-–—.]*\s*", "", text).strip()
    # Remove metropolitan/city info if present
    text = re.sub(r"(?i)^(?:metropolitan|metro)\s*[:\-–—.]*\s*", "", text).strip()
    # Remove address labels that may appear
    text = re.sub(r"(?i)^address\s*[:\-–—.]*\s*", "", text).strip()
    # Remove district info that comes after address
    text = re.sub(r"(?i)\s*[–—-]?\s*(?:district|dist)\s*[:=]*\s*.*$", "", text).strip()
    # Replace commas and other punctuation with spaces
    text = re.sub(r"[,._\-–—]+", " ", text).strip()
    # Remove leading/trailing punctuation.  We avoid stripping Nepali
    # vowel signs (e.g. 'ै', 'ा', etc.) which are classified as non-word by
    # \w; include the Devanagari range explicitly so they are preserved.
    text = re.sub(r"^[^\w\u0900-\u097F]+|[^\w\u0900-\u097F]+$", "", text, flags=re.UNICODE).strip()
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def month_to_number(month_text):
    if not month_text:
        return ""
    month_text = normalize_ocr_text(str(month_text)).upper().strip()
    months = {
        "JAN": "01", "JANUARY": "01",
        "FEB": "02", "FEBRUARY": "02",
        "MAR": "03", "MARCH": "03",
        "APR": "04", "APRIL": "04",
        "MAY": "05",
        "JUN": "06", "JUNE": "06",
        "JUL": "07", "JULY": "07",
        "AUG": "08", "AUGUST": "08",
        "SEP": "09", "SEPTEMBER": "09",
        "OCT": "10", "OCTOBER": "10",
        "NOV": "11", "NOVEMBER": "11",
        "DEC": "12", "DECEMBER": "12",
    }
    if month_text in months:
        return months[month_text]
    for key, value in months.items():
        if month_text.startswith(key[:3]):
            return value
    match = re.search(r"(\d{1,2})", month_text)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 12:
            return str(num).zfill(2)
    return ""

def strip_field_prefix(text, class_id):
    FIELD_PREFIX_PATTERNS = {
        0: [r"issued\s*office", r"office"],
        1: [r"name", r"full\s*name"],
        2: [r"(?:father\s*'?s?)\s*name", r"(?:बुव(?:ाको|ुको)?|बाबु(?:को)?|बुब)(?:को)?(?:\s*नर/?थेर)?",
            r"बुबुको\s*नर/?थेर"],
        3: [r"(?:mother\s*'?s?)\s*name", r"(?:आम(?:ाको|को)?|आमा)(?:\s*को)?(?:\s*नाम(?:\s*थर)?)?",
            r"आमाको\s*नाम(?:\s*थर)?", r"धरः"],
        4: [r"citizenship\s*(?:no|number)"],
        5: [r"full\s*name", r"name"],
        6: [r"sex", r"gender"],
        7: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*year", r"birth\s*year", r"year"],
        8: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*month", r"birth\s*month", r"month"],
        9: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*day", r"birth\s*day", r"day"],
        10: [r"permanent\s*district", r"district"],
        11: [r"permanent\s*address", r"address"],
        12: [r"ward\s*(?:no(?:w|\.)?|number)", r"(?:वर्ड|वर्ड)\s*(?:नं|नंबर|न०)"],
        13: [r"issued\s*date", r"date\s*of\s*issue", r"issue\s*date"],
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


def clean_field_text(text, class_id):
    original = text
    text = normalize_ocr_text(text)
    if class_id == 10:  # perm district
        cleaned = clean_perm_district(text)
        return cleaned
    if class_id == 11:  # perm address
        cleaned = clean_perm_address(text)
        return cleaned
    # address/district prefix handled above
    # remove common OCR garbage (smart quotes, invisible characters)
    text = re.sub(r"[\'\"\u00AD\u200B\u200C\u200D\u2060\uFEFF]", " ", text)
    text = re.sub(r"[–—‐]", "-", text)
    if ":" in text or ";" in text:
        text = re.split(r"[:;]", text)[-1].strip()
    if class_id in [7, 8, 9, 12]:
        text = strip_field_prefix(text, class_id)
        text = re.sub(r'\b(Ye|ye)\s+ar\b', 'Year', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(Da|da)\s+y\b', 'Day', text, flags=re.IGNORECASE)
        text = re.sub(r'^(Month)(\w+)', r'\1 \2', text, flags=re.IGNORECASE)
        text = nepali_to_english_digits(text)
        if class_id == 8:
            month_num = month_to_number(text)
            if month_num:
                return month_num
            numbers = re.findall(r"\d+", text)
            if numbers:
                month_val = int(numbers[0])
                if 1 <= month_val <= 12:
                    return str(month_val).zfill(2)
            return ""
        if class_id == 12:
            digits_only = re.sub(r"[^\d]", "", text).strip()
            if digits_only:
                try:
                    ward_val = int(digits_only)
                    if 1 <= ward_val <= 999:
                        return str(ward_val)
                except:
                    pass
            return ""
        digits = re.sub(r"[^\d]", "", text).strip()
        if class_id == 9 and len(digits) == 1:
            if re.search(r"[IlItT]", text):
                digits = digits * 2
        return digits
    if class_id == 13:
        t = normalize_ocr_text(text)
        t = strip_field_prefix(t, class_id)
        # Convert Nepali digits to English if any remain
        t = nepali_to_english_digits(t)
        # Remove any remaining non-digit, non-dash, non-slash, non-dot characters
        t = re.sub(r"[^0-9/\-\.]", " ", t).strip()
        return t
    if class_id == 6:
        t = normalize_ocr_text(text)
        m = re.search(r"\b(female|male|पुरुष|महिला)\b", t, re.I)
        if m:
            gender_word = m.group(1).lower()
            if gender_word in ('पुरुष', 'male'):
                return 'Male'
            elif gender_word in ('महिला', 'female'):
                return 'Female'
        return ""
    if class_id == 4:
        t = nepali_to_english_digits(text)
        t = re.sub(r"[^0-9\-]", "", t)
        t = re.sub(r"-+", "-", t).strip("-")
        if re.search(r"\d", t):
            return t
        return ""
    text = strip_field_prefix(text, class_id)
    text = strip_generic_leading_label(text)
    text = re.sub(r"^[^\w\u0900-\u097F]+|[^\w\u0900-\u097F]+$", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"\s+", " ", text).strip()
    if class_id in {1, 2, 3, 5}:
        tokens = text.split()
        kept = []
        stop_words = {"name", "full", "father", "mother", "gender", "sex", "dob", "date",
                      "neme", "nemes", "fuh", "ful", "fulll",
                      "namae", "nams", "nam", "nem", "it",
                      "of", "oy", "ofs", "oys", "s"}  # label fragments and prepositions
        for tok in tokens:
            low = tok.lower()
            if low in stop_words:
                continue
            if re.fullmatch(r"[A-Za-z\u0900-\u097F'’\-]+", tok):
                if re.search(r"[A-Z][a-z].*[A-Z]", tok):
                    continue
                if len(tok) == 1 and not re.match(r"[\u0900-\u097F]", tok) and len(tokens) > 1:
                    continue
                if re.search(r"[\u0900-\u097F]", tok):
                    nepali_vowel_marks = "ािीुूृेैोौं:ः"
                    vowel_count = sum(1 for ch in tok if ch in nepali_vowel_marks)
                    total_chars = len(tok)
                    if total_chars > 8 and vowel_count < (total_chars / 6):
                        continue
                kept.append(tok)
        text = " ".join(kept)
        text = text.lower()
        if text in NAME_CORRECTIONS:
            return NAME_CORRECTIONS[text]
        if placeholder.get(class_id, "eng") == "nep":
            m = re.match(r"^(?:\S+\s+)*थर\s+(.+)$", text)
            if m:
                text = m.group(1)
        if placeholder.get(class_id, "eng") == "nep" and not re.search(r"[\u0900-\u097F]", text):
            eng_tokens = [tok for tok in text.split() if re.fullmatch(r"[A-Za-z'’\-]+", tok)]
            if len(eng_tokens) >= 2:
                if eng_tokens[0].lower() == "ne":
                    eng_tokens = eng_tokens[1:]
                return " ".join(eng_tokens)
            return ""
    for _ in range(2):
        if ":" in text or ";" in text:
            text = re.split(r"[:;]", text)[-1].strip()
            text = re.sub(r"^[^\w\u0900-\u097F]+|[^\w\u0900-\u097F]+$", "", text, flags=re.UNICODE).strip()
            if class_id in {1, 2, 3, 5}:
                text = strip_field_prefix(text, class_id)
                text = strip_generic_leading_label(text)
    if class_id == 3:
        text = re.sub(r"धरः\s*", "", text).strip()
        text = re.sub(r"नाम\s*धरः\s*", "", text).strip()
        if re.fullmatch(r"[xX\.\s]{2,}", text):
            return ""
        if text.upper() in ("NA", "N/A", "NONE", "-", "--"):
            return ""
        if re.search(r"\d", text):
            return ""
        if text and not re.search(r"[aeiouAEIOU\u093E-\u094C]", text):
            return ""
        if len(text) < 3:
            return ""
        if re.fullmatch(r"[A-Za-z]+", text) and len(text) <= 4:
            if re.search(r"[bcdfghjklmnpqrstvwxyz]{3,}", text, re.IGNORECASE):
                return ""
    return text


def strip_generic_leading_label(text):
    """Remove a leading label such as "District:" or "Address:" from OCR output."""
    # First try: short 1-2 word label followed by a separator
    match = re.match(
        r'^\s*([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)?)\s*[:;._\-–—_\"\'"?]+\s*(.+)$',
        text,
    )
    if match:
        return match.group(2).strip()
    # Fall back: longer label up to ~40 chars
    match = re.match(
        r'^\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{1,40})\s*[:;._\-–—_\"\'“”?]+\s*(.+)$',
        text,
    )
    if match:
        return match.group(2).strip()
    return text


def extract_nagrikta_number(fields, min_len=4):
    if not fields:
        return ""
    for fld in fields:
        txt = fld.get('text') if isinstance(fld, dict) else str(fld)
        if not txt:
            continue
        txt = nepali_to_english_digits(str(txt))
        for m in re.finditer(r"(\d{1,})", txt):
            s = m.group(1)
            if len(s) >= min_len:
                return s.lstrip('0') or s
    return ""
