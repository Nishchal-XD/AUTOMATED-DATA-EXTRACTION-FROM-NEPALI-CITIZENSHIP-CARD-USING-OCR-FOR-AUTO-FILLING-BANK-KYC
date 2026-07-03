#!/usr/bin/env python3
"""Test actual extraction flow and form prefill"""
import os
from pathlib import Path
from PIL import Image
from main import get_model, preprocess_image, ocr_text, clean_field_text, placeholder

upload_folder = 'uploads'

# Find latest images (not crops)
images = sorted(
    list(Path(upload_folder).glob('*.png')) + 
    list(Path(upload_folder).glob('*.jpg')) + 
    list(Path(upload_folder).glob('*.jpeg')),
    key=lambda p: p.stat().st_mtime, reverse=True
)
images = [img for img in images if not img.name.startswith('crop_')][:2]  # Get last 2 (front/back)

if len(images) < 2:
    print(f"Need at least 2 images (front/back), found {len(images)}")
    exit(1)

print("=" * 80)
print("FULL EXTRACTION FLOW TEST")
print("=" * 80)
print(f"\nTest images:")
for img in images:
    print(f"  {img.name}")

# Simulate the upload endpoint
final_output = {"front": [], "back": []}
labels = ["front", "back"]
imgs = [Image.open(img).convert("RGB") for img in images]

model = get_model()

for label, img in zip(labels, imgs):
    print(f"\n[{label.upper()}]")
    results = model.predict(source=[img], conf=0.5)
    boxes = getattr(results[0], 'boxes', None)
    boxes_list = boxes.data.tolist() if boxes is not None else []
    print(f"  Found {len(boxes_list)} detection boxes")
    
    for i, box in enumerate(boxes_list):
        try:
            x1, y1, x2, y2 = map(int, box[:4])
            conf = float(box[4]) if len(box) > 4 else 0.0
            class_id = int(box[5]) if len(box) > 5 else 0
            
            crop_img = img.crop((x1, y1, x2, y2))
            lang = placeholder.get(class_id, "eng")
            tess_lang = "nep" if lang == "nep" else "eng"
            
            # Preprocess
            crop = preprocess_image(crop_img, tess_lang)
            
            # OCR
            text = ocr_text(crop, tess_lang)
            
            # Clean
            cleaned_text = clean_field_text(text, class_id)
            
            final_output[label].append({
                "class_id": class_id,
                "text": cleaned_text,
                "raw": text[:50] if text else "(empty)"
            })
            
            print(f"    Class {class_id:2d} [{tess_lang}] conf={conf:.3f}: '{cleaned_text[:40]}'")
        except Exception as e:
            print(f"    Box {i} error: {e}")

# Now simulate prefill logic
print("\n[PREFILL CONSTRUCTION]")
def get_text(data_list, class_id):
    for item in data_list:
        if item.get("class_id") == class_id and item.get("text"):
            return item["text"]
    return ""

prefill = {
    "fullname": get_text(final_output.get("back", []), 5),
    "father_name": get_text(final_output.get("front", []), 2),
    "mother_name": get_text(final_output.get("front", []), 3),
    "docnum": get_text(final_output.get("back", []), 4),
    "gender": get_text(final_output.get("back", []), 6),
    "perm_district": get_text(final_output.get("back", []), 10),
    "perm_address": get_text(final_output.get("back", []), 11),
    "perm_ward_no": get_text(final_output.get("back", []), 12),
}

print(f"  Fullname: {prefill['fullname']}")
print(f"  Father: {prefill['father_name']}")
print(f"  Mother: {prefill['mother_name']}")
print(f"  Doc No: {prefill['docnum']}")
print(f"  Gender: {prefill['gender']}")
print(f"  District: {prefill['perm_district']}")
print(f"  Address: {prefill['perm_address']}")
print(f"  Ward: {prefill['perm_ward_no']}")

print("\n" + "=" * 80)
