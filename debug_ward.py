import json
from main import clean_field_text

# Load cached data
with open('cache/kyc_1240e17c-ce11-4788-8fc5-138ba3e54679.json', encoding='utf-8') as f:
    data = json.load(f)

# Check back side for class_id 12 (ward_no)
back_data = data['extracted_data']['back']

# Test all back fields
print("Back side field cleaning:")
print("=" * 70)
for item in back_data:
    cid = item.get('class_id')
    raw = item.get('text')
    cleaned = clean_field_text(raw, cid)
    label = {0:'office',1:'nepname',2:'father',3:'mother',4:'docnum',5:'fullname',6:'gender',7:'year',8:'month',9:'day',10:'district',11:'address',12:'ward',13:'issued'}.get(cid, '?')
    print(f"class_id {cid:2d} ({label:10s}): '{raw}' → '{cleaned}'")

# Special highlight for ward
print("\n" + "=" * 70)
print("WARD NUMBER FIELD EXTRACTION TEST:")
for item in back_data:
    if item.get('class_id') == 12:
        raw = item.get('text')
        cleaned = clean_field_text(raw, 12)
        print(f"  Raw:     '{raw}'")
        print(f"  Cleaned: '{cleaned}'")
        print(f"  Status:  {'✓ EXTRACTED' if cleaned else '✗ EMPTY'}")
        break
else:
    print("  ✗ No class_id 12 detected in YOLO results")

