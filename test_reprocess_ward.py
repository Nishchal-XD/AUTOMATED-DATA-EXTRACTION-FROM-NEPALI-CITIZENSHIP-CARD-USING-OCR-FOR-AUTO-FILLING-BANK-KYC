import json, os, glob
from PIL import Image
from main import ocr_text, preprocess_for_numbers, preprocess_for_nepali, placeholder, clean_field_text
import numpy as np

# We'll re-run OCR on existing crops to see if empty strings now produce digits

cache_files = glob.glob('cache/kyc_*.json')[:20]

results = []

for filepath in cache_files:
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
    for item in data.get('extracted_data', {}).get('back', []):
        if item.get('class_id') == 12:
            raw = item.get('text','')
            conf = item.get('confidence')
            # we don't have the image crop so we can't re-run easily
            results.append((os.path.basename(filepath), raw, conf))

print('Collected ward raw text from cache:')
for r in results[:10]:
    print(r)

print('\nNote: without the original crop image, we cannot re-run OCR on cache.\n')
print('To properly test, re-upload a failing image or modify diagnose script to rerun YOLO on stored images.')