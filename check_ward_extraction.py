import json
import glob

files = glob.glob('cache/kyc_*.json')[:20]
with_ward = 0
without_ward = 0
ward_values = []

for f in files:
    try:
        d = json.load(open(f, encoding='utf-8'))
        ward_items = [x for x in d.get('extracted_data', {}).get('back', []) if x.get('class_id') == 12]
        if ward_items:
            with_ward += 1
            for item in ward_items:
                ward_values.append(item.get('text', ''))
        else:
            without_ward += 1
    except Exception as e:
        print(f"Error reading {f}: {e}")

print(f"Checked {len(files)} files:")
print(f"  Files with ward (class_id=12): {with_ward}")
print(f"  Files without ward: {without_ward}")
print(f"  Ward values extracted: {ward_values[:10]}")
