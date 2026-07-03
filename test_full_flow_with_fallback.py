#!/usr/bin/env python3
"""Test full extraction flow WITH fallback (as upload endpoint does)"""
import os
from pathlib import Path
from PIL import Image
from main import get_model, preprocess_image, ocr_text, clean_field_text, extract_nagrikta_number, placeholder

upload_folder = 'uploads'

# Find latest images (try to identify front/back by name first)
all_imgs = sorted(
    list(Path(upload_folder).glob('*.png')) +
    list(Path(upload_folder).glob('*.jpg')) +
    list(Path(upload_folder).glob('*.jpeg')),
)
all_imgs = [img for img in all_imgs if not img.name.startswith('crop_')]
front_img = next((img for img in all_imgs if 'front' in img.name.lower()), None)
back_img = next((img for img in all_imgs if 'back' in img.name.lower()), None)
if front_img and back_img:
    images = [front_img, back_img]
else:
    images = sorted(all_imgs, key=lambda p: p.stat().st_mtime, reverse=True)[:2]

imgs = [Image.open(img).convert("RGB") for img in images]

labels = ["front", "back"]

final_output = {"front": [], "back": []}

model = get_model()

for label, img in zip(labels, imgs):
    print(f"\n[{label.upper()}]")
    
    # Primary detection
    results = model.predict(source=[img], conf=0.5)
    boxes = getattr(results[0], 'boxes', None)
    boxes_list = boxes.data.tolist() if boxes is not None else []
    print(f"  Primary detect: {len(boxes_list)} boxes")
    
    # Fallback detection + full-image OCR if needed
    synthetic_full_text = None
    if not boxes_list:
        print(f"  → No boxes found, trying fallback...")
        try:
            relaxed = model.predict(source=[img], conf=0.2)
            boxes = getattr(relaxed[0], 'boxes', None)
            boxes_list = boxes.data.tolist() if boxes is not None else []
            print(f"    Fallback detect: {len(boxes_list)} boxes at conf=0.2")
        except Exception as e:
            print(f"    Fallback detect error: {e}")
        
        # Full-image OCR
        try:
            tess_lang = "eng"  # assume English for back
            full_crop = preprocess_image(img, tess_lang)
            full_text = ocr_text(full_crop, tess_lang, is_full_page=True)
            synthetic_full_text = full_text
            
            found_num = extract_nagrikta_number([{'text': full_text}])
            print(f"    Full-image OCR: {len(full_text)} chars")
            if found_num:
                boxes_list.append([0, 0, img.width, img.height, 1.0, 4])
                print(f"    ✓ Found nagrikta: {found_num}")
        except Exception as e:
            print(f"    Full-image OCR error: {e}")
            import traceback
            traceback.print_exc()
    
    # Process all boxes
    print(f"  Processing {len(boxes_list)} boxes...")
    for i, box in enumerate(boxes_list):
        try:
            x1, y1, x2, y2 = map(int, box[:4])
            conf = float(box[4]) if len(box) > 4 else 0.0
            class_id = int(box[5]) if len(box) > 5 else 0
            
            lang = placeholder.get(class_id, "eng")
            tess_lang = "nep" if lang == "nep" else "eng"
            
            # Use synthetic text for full-image box
            if synthetic_full_text and class_id == 4 and x1 == 0 and y1 == 0 and x2 == img.width and y2 == img.height:
                text = synthetic_full_text
            else:
                crop_img = img.crop((x1, y1, x2, y2))
                crop = preprocess_image(crop_img, tess_lang)
                text = ocr_text(crop, tess_lang)
            
            cleaned_text = clean_field_text(text, class_id)
            
            if cleaned_text:
                final_output[label].append({
                    "class_id": class_id,
                    "text": cleaned_text,
                })
                print(f"    Class {class_id:2d}: '{cleaned_text[:40]}'")
        except Exception as e:
            print(f"    Box {i} error: {e}")

# Prefill
print("\n[PREFILL]")
def get_text(data_list, class_id):
    for item in data_list:
        if item.get("class_id") == class_id and item.get("text"):
            return item["text"]
    return ""

prefill = {
    "fullname": get_text(final_output.get("back", []), 5),
    "docnum": get_text(final_output.get("back", []), 4),
    "gender": get_text(final_output.get("back", []), 6),
}

for k, v in prefill.items():
    print(f"  {k}: {'✓ ' + v[:50] if v else '(empty)'}")

print("\n" + "=" * 80)
