#!/usr/bin/env python3
"""Debug extraction pipeline end-to-end with your uploaded images"""
import os
import sys
from PIL import Image
from pathlib import Path
from main import get_model, preprocess_image, ocr_text, clean_field_text, extract_nagrikta_number, placeholder

# Find uploaded images
upload_folder = 'uploads'
images = list(Path(upload_folder).glob('*.png')) + list(Path(upload_folder).glob('*.jpg')) + list(Path(upload_folder).glob('*.jpeg'))
images = [img for img in images if not img.name.startswith('crop_')]  # exclude crops

print("=" * 80)
print("EXTRACTION PIPELINE DEBUG")
print("=" * 80)
print(f"\nFound {len(images)} uploaded image(s)")

if not images:
    print("No uploaded images found in 'uploads' folder")
    sys.exit(1)

# Test on first found image
test_img = sorted(images)[-1]  # Use most recent
print(f"\nTesting with: {test_img}")

try:
    front_img = Image.open(test_img).convert("RGB")
    print(f"✓ Image loaded: {front_img.size}")
except Exception as e:
    print(f"✗ Failed to load image: {e}")
    sys.exit(1)

# Step 1: YOLO prediction
print("\n[STEP 1] YOLO Detection...")
try:
    model = get_model()
    print(f"  ✓ Model loaded")
    results = model.predict(source=[front_img], conf=0.5)
    boxes = getattr(results[0], 'boxes', None)
    boxes_list = boxes.data.tolist() if boxes is not None else []
    print(f"  ✓ YOLO prediction completed")
    print(f"  → Found {len(boxes_list)} boxes at conf=0.5")
    
    if boxes_list:
        for i, box in enumerate(boxes_list[:3]):  # Show first 3
            print(f"    Box {i}: conf={box[4]:.3f}, class={int(box[5])}")
except Exception as e:
    print(f"  ✗ YOLO prediction failed: {e}")
    import traceback
    traceback.print_exc()
    boxes_list = []

# Step 2: Fallback detection if needed
if not boxes_list:
    print("\n[STEP 2] Fallback Detection (conf=0.2)...")
    try:
        relaxed = model.predict(source=[front_img], conf=0.2)
        boxes = getattr(relaxed[0], 'boxes', None)
        boxes_list = boxes.data.tolist() if boxes is not None else []
        print(f"  → Found {len(boxes_list)} boxes at conf=0.2")
        if boxes_list:
            for i, box in enumerate(boxes_list[:3]):
                print(f"    Box {i}: conf={box[4]:.3f}, class={int(box[5])}")
    except Exception as e:
        print(f"  ✗ Fallback detection failed: {e}")
        boxes_list = []

# Step 3: Full-image OCR fallback
print("\n[STEP 3] Full-Image OCR Fallback...")
try:
    tess_lang = "eng"
    full_crop = preprocess_image(front_img, tess_lang)
    print(f"  ✓ Image preprocessed")
    
    full_text = ocr_text(full_crop, tess_lang)
    print(f"  ✓ OCR completed")
    print(f"  → Raw OCR text length: {len(full_text)} chars")
    if full_text:
        print(f"  → First 100 chars: {full_text[:100]}")
    
    # Try to extract nagarikta number
    found_num = extract_nagrikta_number([{'text': full_text}])
    print(f"  → Nagarikta number found: {found_num if found_num else 'NONE'}")
    
    # Clean the full text as name field
    cleaned = clean_field_text(full_text, 5)  # class_id 5 = fullname
    print(f"  → Cleaned name (class 5): {cleaned}")
    
except Exception as e:
    print(f"  ✗ Full-image OCR failed: {e}")
    import traceback
    traceback.print_exc()
    full_text = ""

# Step 4: Test OCR on individual fields if we had boxes
print("\n[STEP 4] Individual Field OCR (sample)...")
if boxes_list:
    try:
        x1, y1, x2, y2 = map(int, boxes_list[0][:4])
        class_id = int(boxes_list[0][5]) if len(boxes_list[0]) > 5 else 0
        
        crop = front_img.crop((x1, y1, x2, y2))
        print(f"  Crop size: {crop.size}")
        
        lang = placeholder.get(class_id, "eng")
        tess_lang = "nep" if lang == "nep" else "eng"
        
        processed = preprocess_image(crop, tess_lang)
        text = ocr_text(processed, tess_lang)
        cleaned = clean_field_text(text, class_id)
        
        print(f"  Class {class_id} [{tess_lang}]: raw={text[:50]}, cleaned={cleaned}")
    except Exception as e:
        print(f"  ✗ Field OCR failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("END DEBUG")
print("=" * 80)
