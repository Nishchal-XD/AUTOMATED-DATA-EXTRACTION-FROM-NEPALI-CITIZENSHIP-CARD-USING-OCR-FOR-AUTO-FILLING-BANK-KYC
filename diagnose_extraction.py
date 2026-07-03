"""
Diagnostic script to check what fields are being detected and extracted
from uploaded Nagarikta images. Run this after uploading an image.
"""
import json
import os
from main import clean_field_text

# Find the most recent cached OCR output
cache_dir = 'cache'
if os.path.exists(cache_dir):
    files = [f for f in os.listdir(cache_dir) if f.startswith('kyc_') and f.endswith('.json')]
    if files:
        latest_file = sorted(files)[-1]
        filepath = os.path.join(cache_dir, latest_file)
        
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
        
        print("=" * 80)
        print(f"DIAGNOSTIC REPORT: {latest_file}")
        print("=" * 80)
        
        for side in ['front', 'back']:
            print(f"\n{side.upper()} SIDE:")
            print("-" * 80)
            fields = data['extracted_data'][side]
            
            if not fields:
                print(f"  No fields detected on {side} side!")
                continue
            
            field_names = {
                0: 'Issued Office', 1: 'Name (Nepali)', 2: 'Father Name',
                3: 'Mother Name', 4: 'Citizenship No', 5: 'Full Name (Eng)',
                6: 'Gender', 7: 'DOB Year', 8: 'DOB Month', 9: 'DOB Day',
                10: 'Perm District', 11: 'Perm Address', 12: 'Perm Ward No',
                13: 'Issued Date'
            }
            
            for item in fields:
                cid = item.get('class_id')
                raw = item.get('text', '')
                conf = item.get('confidence', 0)
                cleaned = clean_field_text(raw, cid)
                
                fname = field_names.get(cid, f'Field {cid}')
                status = '✓' if cleaned else '✗'
                
                print(f"  {status} [{cid:2d}] {fname:18s} | conf: {conf:.3f}")
                print(f"       Raw:     {raw}")
                print(f"       Cleaned: {cleaned}")
        
        print("\n" + "=" * 80)
        print("MISSING FIELDS ANALYSIS:")
        print("=" * 80)
        
        all_cids = set()
        for side in ['front', 'back']:
            for item in data['extracted_data'][side]:
                all_cids.add(item.get('class_id'))
        
        expected_on_back = {7, 8, 9, 10, 11, 12, 13, 4, 5, 6}
        missing_on_back = expected_on_back - all_cids
        
        if 12 in missing_on_back:
            print("✗ Ward Number (class_id 12) NOT DETECTED on back side")
            print("  → This is the root cause of perm_ward_no being empty!")
            print("\n  ACTION REQUIRED: Model training may be needed")
            print("  Possible causes:")
            print("  1. Ward number is not clearly visible on the card")
            print("  2. YOLO model has not been trained on cards with this layout")
            print("  3. Card image quality is too low")
        else:
            print("✓ Ward Number (class_id 12) was detected")
            for item in data['extracted_data']['back']:
                if item.get('class_id') == 12:
                    cleaned = clean_field_text(item.get('text', ''), 12)
                    if not cleaned:
                        print(f"  ⚠ But cleaning produced empty result")
                        print(f"    Raw text: {item.get('text')}")
        
        for cid in sorted(missing_on_back):
            cname = field_names.get(cid, f'Field {cid}')
            print(f"✗ Missing: [{cid:2d}] {cname}")
    else:
        print("No cached OCR files found")
else:
    print("Cache directory not found")
