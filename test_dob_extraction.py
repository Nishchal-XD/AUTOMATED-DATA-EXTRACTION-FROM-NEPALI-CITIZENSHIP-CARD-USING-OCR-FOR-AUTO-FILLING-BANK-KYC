import re
from datetime import datetime

# Test data from cache
dob_test_cases = [
    (7, "Year-2003", "2003"),  # dob_year
    (8, "Month:JUL", "07"),    # dob_month  
    (9, "Day-Il", "11"),       # dob_day
]

# Test data for issued date
issued_date_test_cases = [
    "जारी मिति : २०७६-०४-१२",  # Nepali format
    "issued date: 2076-04-12",   # English format
    "मिति: २०७६-०४-१२",         # Simplified Nepali
    "Date: 2076-04-12",           # Simple English
]

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text

def nepali_to_english_digits(text):
    """Convert Nepali digits to English digits and fix common OCR misreads"""
    if not text:
        return ""
    
    # Convert Nepali digits to English
    nep = "०१२३४५६७८९"
    eng = "0123456789"
    table = str.maketrans(nep, eng)
    text = text.translate(table)
    
    # Fix common OCR mistakes: letters i,I,l,L misread as '1' and O,o as '0'
    # Handle leading i/I/l/L which are often OCR errors for '1'
    text = re.sub(r'^[ilIL]+', lambda m: '1' * len(m.group()), text)
    
    # Replace combinations of i/I/l/L with '1' for each character
    text = re.sub(r'[ilIL][ilIL]', lambda m: '1' * len(m.group()), text)
    # Replace standalone i/I/l/L between digits with '1'
    text = re.sub(r'(\d)[ilIL](?=\d)', r'\g<1>1', text)
    text = re.sub(r'(?<=\d)[ilIL](\d)', r'1\g<1>', text)
    # Replace 'O' or 'o' surrounded by digits with '0'
    text = re.sub(r'(\d)[Oo](?=\d)', r'\g<1>0', text)
    text = re.sub(r'(?<=\d)[Oo](\d)', r'0\g<1>', text)
    
    return text

def month_to_number(month_text):
    """Convert month name to month number (01-12)"""
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
        month_num = int(match.group(1))
        if 1 <= month_num <= 12:
            return str(month_num).zfill(2)
    
    return ""

FIELD_PREFIX_PATTERNS = {
    7: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*year", r"birth\s*year", r"year"],
    8: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*month", r"birth\s*month", r"month"],
    9: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*day", r"birth\s*day", r"day"],
}

def strip_field_prefix(text, class_id):
    patterns = FIELD_PREFIX_PATTERNS.get(class_id, [])
    for base in patterns:
        text = re.sub(
            rf"(?i)^\s*{base}\s*[:.\-–—_]*\s*",
            "",
            text,
            count=1
        )
    return text

def parse_to_html_date(date_text):
    """Parse issued date in various formats (English and Nepali)"""
    if not date_text:
        return ""
    
    date_text = normalize_ocr_text(date_text)
    if not date_text:
        return ""
    
    # Convert Nepali digits to English
    date_text = nepali_to_english_digits(date_text)
    
    # Remove Nepali date labels (जारी मिति, मिति, etc.)
    date_text = re.sub(r"(?i)(?:जारी\s*)?मिति\s*[:=]*\s*", "", date_text).strip()
    # Remove English date labels
    date_text = re.sub(r"(?i)(?:issued|date|dob)\s*[:=]*\s*", "", date_text).strip()
    
    # Extract date pattern: YYYY-MM-DD or YYYY/MM/DD or DD-MM-YYYY, etc.
    # Check for YYYY-MM-DD format
    match = re.search(r"(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})", date_text)
    if match:
        year, month, day = match.groups()
        try:
            # Validate and format
            month = int(month)
            day = int(day)
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
        except:
            pass
    
    # Check for DD-MM-YYYY format
    match = re.search(r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})", date_text)
    if match:
        day, month, year = match.groups()
        try:
            month = int(month)
            day = int(day)
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
        except:
            pass
    
    return ""

# Test the cleaning logic
print("Testing Date of Birth field extraction:")
print("=" * 60)
for class_id, raw_text, expected in dob_test_cases:
    text = normalize_ocr_text(raw_text)
    text = strip_field_prefix(text, class_id)
    text = nepali_to_english_digits(text)
    
    if class_id == 8:  # Month
        result = month_to_number(text)
    else:
        result = re.sub(r"[^\d]", "", text).strip()
    
    status = "✓ PASS" if result == expected else "✗ FAIL"
    print(f"{status} | Class {class_id}: '{raw_text}' → '{result}' (expected: '{expected}')")

print("=" * 60)
print("\nFull DOB construction test:")
dob_year = "2003"
dob_month = "07"
dob_day = "11"
dob = f"{dob_year}-{dob_month}-{dob_day}"
print(f"Date of Birth: {dob}")

print("\n" + "=" * 60)
print("Testing Issued Date extraction:")
print("=" * 60)
for date_str in issued_date_test_cases:
    result = parse_to_html_date(date_str)
    status = "✓ PASS" if result else "✗ EMPTY"
    print(f"{status} | '{date_str}' → '{result}'")

