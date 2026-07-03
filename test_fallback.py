#!/usr/bin/env python3
"""Test fallback detection on front3.jpg and back3.jpg"""
from PIL import Image
from main import get_model, preprocess_image, ocr_text, extract_nagrikta_number

model = get_model()

for filename in ['uploads/front3.jpg', 'uploads/back3.jpg']:
    print(f"\n{'=' * 60}")
    print(f"Testing: {filename}")
    print('=' * 60)
    
    img = Image.open(filename).convert("RGB")
    print(f"Size: {img.size}")
    
    # Primary detection
    print("\n1. Primary detection (conf=0.5)...")
    results = model.predict(source=[img], conf=0.5)
    boxes = getattr(results[0], 'boxes', None)
    boxes_list = boxes.data.tolist() if boxes is not None else []
    print(f"   Found {len(boxes_list)} boxes")
    
    # Fallback detection
    if not boxes_list:
        print("\n2. Fallback detection (conf=0.2)...")
        results = model.predict(source=[img], conf=0.2)
        boxes = getattr(results[0], 'boxes', None)
        boxes_list = boxes.data.tolist() if boxes is not None else []
        print(f"   Found {len(boxes_list)} boxes")
    
    # Full-image OCR
    print("\n3. Full-image OCR...")
    try:
        crop = preprocess_image(img, "eng")
        text = ocr_text(crop, "eng")
        print(f"   OCR text length: {len(text)} chars")
        if text:
            print(f"   First 100 chars: {text[:100]}")
        
        # Extract nagarikta
        num = extract_nagrikta_number([{'text': text}])
        print(f"   Nagarikta number: {num if num else 'NONE'}")
    except Exception as e:
        print(f"   OCR error: {e}")

    # Ward fallback test
    print("\n4. Ward fallback scan on full image")
    fulltext = ocr_text(img, 'eng') + ' ' + ocr_text(img, 'nep')
    m = re.search(r"ward\s*(?:no(?:w|\.)?|number)?\D*(\d{1,3})", fulltext, flags=re.I)
    if m:
        print(f"   Found ward via regex: '{m.group(0)}' -> {m.group(1)}")
    else:
        print("   No ward pattern found in full-text")
