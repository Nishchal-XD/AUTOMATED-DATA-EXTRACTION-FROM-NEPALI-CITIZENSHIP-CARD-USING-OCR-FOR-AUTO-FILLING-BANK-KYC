#!/usr/bin/env python3
"""Test ocr_text function directly vs pytesseract"""
from PIL import Image
from main import preprocess_image, ocr_text
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = Image.open('uploads/back3.jpg').convert("RGB")
print(f"Image size: {img.size}")

# Method 1: Direct pytesseract (as in test_preprocess_debug.py)
print("\n[Method 1] Direct pytesseract.image_to_string...")
preprocessed = preprocess_image(img, "eng")
text1 = pytesseract.image_to_string(preprocessed, lang='eng', config="--oem 1 --psm 7")
print(f"  Result: {len(text1)} chars")
print(f"  Text: {text1[:100]}")

# Method 2: Using ocr_text function (as in fallback code)
print("\n[Method 2] Using ocr_text() function...")
preprocessed = preprocess_image(img, "eng")
text2 = ocr_text(preprocessed, "eng")
print(f"  Result: {len(text2)} chars")
print(f"  Text: {text2[:100] if text2 else '(empty)'}")

# Check if it's a backend issue
from main import OCR_BACKEND
print(f"\n[Config] OCR_BACKEND = {OCR_BACKEND}")

# Method 3: Check what happens with tess_lang variants
print("\n[Method 3] Try different language codes...")
for lang in ['eng', 'nep+eng', 'eng+nep']:
    text = ocr_text(preprocessed, lang)
    print(f"  lang='{lang}': {len(text)} chars -> {text[:50] if text else '(empty)'}")
