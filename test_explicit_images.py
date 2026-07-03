#!/usr/bin/env python3
"""Test extraction for explicitly front3 and back3 images"""
from PIL import Image
from main import get_model, preprocess_image, ocr_text, clean_field_text, extract_nagrikta_number, placeholder

print("=" * 80)
print("EXPLICIT FRONT3 + BACK3 EXTRACTION TEST")
print("=" * 80)

final_output = {"front": [], "back": []}
img_paths = {
    "front": "uploads/front3.jpg",
    "back": "uploads/back3.jpg",
}

model = get_model()

for key, img_path in img_paths.items():
    print(f"\n[{key.upper()}: {img_path}]")
    
    img = Image.open(img_path).convert("RGB")
    print(f"  Size: {img.size}")
    
    # Primary detection
    results = model.predict(source=[img], conf=0.5)
    boxes = getattr(results[0], 'boxes', None)
    boxes_list = boxes.data.tolist() if boxes is not None else []
    print(f"  Boxes at conf=0.5: {len(boxes_list)}")
    
    # Fallback
    synthetic_full_text = None
    if not boxes_list:
        try:
            relaxed = model.predict(source=[img], conf=0.2)
            boxes = getattr(relaxed[0], 'boxes', None)
            boxes_list = boxes.data.tolist() if boxes is not None else []
            print(f"  Boxes at conf=0.2 (fallback): {len(boxes_list)}")
        except:
            pass
        
        try:
            full_crop = preprocess_image(img, "eng")
            full_text = ocr_text(full_crop, "nep+eng", is_full_page=True)
            synthetic_full_text = full_text
            print(f"  Full-image OCR: {len(full_text)} chars")
            print(f"  First 100 chars: {full_text[:100]}")
            
            found_num = extract_nagrikta_number([{'text': full_text}])
            if found_num:
                boxes_list.append([0, 0, img.width, img.height, 1.0, 4])
                print(f"  ✓ Extracted nagrikta: {found_num}")
        except Exception as e:
            print(f"  Full-image OCR error: {e}")
            import traceback
            traceback.print_exc()
    
    # Process boxes
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
            
            final_output[key].append({
                "class_id": class_id,
                "text": cleaned_text,
            })
            
            print(f"  Class {class_id}: '{cleaned_text[:50]}'")
        except Exception as e:
            print(f"  Box {i} error: {e}")

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
    print(f"  {k}: {'✓ ' + v if v else '(empty)'}")

print("\n" + "=" * 80)
