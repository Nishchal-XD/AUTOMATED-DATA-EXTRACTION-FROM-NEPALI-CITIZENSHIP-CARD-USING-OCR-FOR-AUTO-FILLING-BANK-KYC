#!/usr/bin/env python3
"""Debug back3.jpg OCR specifically"""
from PIL import Image
from main import preprocess_image, ocr_text

img = Image.open('uploads/back3.jpg').convert("RGB")
print(f"Image: {img.size}")

# Test different language combinations
langs = ['eng', 'nep', 'nep+eng', 'eng+nep']
for lang in langs:
    try:
        crop = preprocess_image(img, "eng")
        text = ocr_text(crop, lang, is_full_page=True)
        print(f"\nlang='{lang}':")
        print(f"  Chars: {len(text)}")
        print(f"  Text: {text[:100] if text else '(empty)'}")
    except Exception as e:
        print(f"\nlang='{lang}': ERROR {e}")
