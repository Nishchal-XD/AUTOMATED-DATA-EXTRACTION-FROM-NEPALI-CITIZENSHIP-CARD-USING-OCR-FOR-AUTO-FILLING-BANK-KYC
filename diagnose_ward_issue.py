"""
Diagnostic tool to identify ward number extraction issues
"""
import json
import os
import glob
from pathlib import Path

# Include clean_field_text inline to avoid importing Flask-heavy main.py
import re

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[©®™•·]", "", text)
    return text

def nepali_to_english_digits(text):
    if not text:
        return ""
    nep = "०१२३४५६७८९"
    eng = "0123456789"
    table = str.maketrans(nep, eng)
    text = text.translate(table)
    text = re.sub(r'^[ilIL]+', lambda m: '1' * len(m.group()), text)
    text = re.sub(r'[ilIL][ilIL]', lambda m: '1' * len(m.group()), text)
    text = re.sub(r'(\d)[ilIL](?=\d)', r'\g<1>1', text)
    text = re.sub(r'(?<=\d)[ilIL](\d)', r'1\g<1>', text)
    text = re.sub(r'(\d)[Oo](?=\d)', r'\g<1>0', text)
    text = re.sub(r'(?<=\d)[Oo](\d)', r'0\g<1>', text)
    return text

def strip_field_prefix(text, class_id):
    FIELD_PREFIX_PATTERNS = {
        12: [r"ward\s*(?:no(?:w|\.)?|number)", r"(?:वर्ड|वर्ड)\s*(?:नं|नंबर|न०)"],
    }
    patterns = FIELD_PREFIX_PATTERNS.get(class_id, [])
    for base in patterns:
        text = re.sub(
            rf"(?i)^\s*{base}\s*[:./\-–—_]*\s*",
            "",
            text,
            count=1
        )
    return text

def clean_field_text(text, class_id):
    """Clean OCR text for class_id 12 (ward number)"""
    if class_id != 12:
        return text
    
    original = text
    text = normalize_ocr_text(text)
    
    if ":" in text or ";" in text:
        text = re.split(r"[:;]", text)[-1].strip()
    
    text = strip_field_prefix(text, class_id)
    text = nepali_to_english_digits(text)
    
    digits_only = re.sub(r"[^\d]", "", text).strip()
    
    if digits_only:
        try:
            ward_val = int(digits_only)
            if 1 <= ward_val <= 999:
                return str(ward_val)
        except:
            pass
    
    return ""

def diagnose_ward_extraction():
    """Check all cached KYC data for ward extraction issues"""
    cache_dir = 'cache'
    
    if not os.path.exists(cache_dir):
        print("✗ Cache directory not found")
        return
    
    files = sorted(glob.glob(os.path.join(cache_dir, 'kyc_*.json')))[:30]
    
    if not files:
        print("✗ No cache files found")
        return
    
    print("=" * 80)
    print("WARD NUMBER EXTRACTION DIAGNOSTIC")
    print("=" * 80)
    
    detected = 0
    not_detected = 0
    empty_ocr = 0
    cleaning_failed = 0
    success = 0
    
    issues = []
    
    for filepath in files:
        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
            
            back_data = data.get('extracted_data', {}).get('back', [])
            ward_items = [x for x in back_data if x.get('class_id') == 12]
            
            if not ward_items:
                not_detected += 1
                issues.append(('NOT_DETECTED', filepath, None, None))
            else:
                detected += 1
                for ward_item in ward_items:
                    raw_text = ward_item.get('text', '')
                    conf = ward_item.get('confidence', 0)
                    
                    if not raw_text.strip():
                        empty_ocr += 1
                        issues.append(('EMPTY_OCR', filepath, '', conf))
                    else:
                        cleaned = clean_field_text(raw_text, 12)
                        if not cleaned:
                            cleaning_failed += 1
                            issues.append(('CLEANING_FAILED', filepath, raw_text, conf))
                        else:
                            success += 1
        except Exception as e:
            print(f"⚠ Error reading {filepath}: {e}")
    
    total = len(files)
    print(f"\nSUMMARY ({total} files checked):")
    print(f"  ✓ Successfully extracted ward numbers: {success}")
    print(f"  ⚠ Detected but cleaning failed: {cleaning_failed}")
    print(f"  ⚠ Detected with empty OCR text: {empty_ocr}")
    print(f"  ✗ Ward field NOT detected by YOLO: {not_detected}")
    print(f"  ✗ Model detection rate: {detected}/{total} = {100*detected/total:.1f}%")
    
    print("\n" + "=" * 80)
    print("ISSUE BREAKDOWN:")
    print("=" * 80)
    
    if not_detected > 0:
        print(f"\n1. MISSING FIELD DETECTION (Most Critical): {not_detected} files")
        print("   → YOLO model not detecting ward field on these cards")
        print("   → ROOT CAUSE: Model may not be trained for your card layout")
        print("   → FIX: Need to retrain YOLO model with labeled ward fields")
        print("   → WORKAROUND: Add manual ward entry field in form")
    
    if empty_ocr > 0:
        print(f"\n2. EMPTY OCR RESULTS: {empty_ocr} files")
        print("   → Ward field detected but OCR returned empty text")
        print("   → CAUSE: Bad image quality or field visibility")
        print("   → SUGGESTION: Check/improve image preprocessing")
    
    if cleaning_failed > 0:
        print(f"\n3. CLEANING FAILURES: {cleaning_failed} files")
        print("   → OCR got text but extraction logic returned empty")
        print("   Sample issue texts:")
        for issue_type, filepath, text, conf in issues:
            if issue_type == 'CLEANING_FAILED':
                fname = os.path.basename(filepath)
                print(f"     {fname}: '{text}' (conf: {conf:.3f})")
                break
    
    print("\n" + "=" * 80)
    print("DETAILED ISSUES:")
    print("=" * 80)
    
    for issue_type, filepath, text, conf in sorted(issues, key=lambda x: x[0])[:5]:
        fname = os.path.basename(filepath)
        if issue_type == 'NOT_DETECTED':
            print(f"\n✗ {fname}")
            print("  Issue: Ward field not detected by YOLO model")
        elif issue_type == 'EMPTY_OCR':
            print(f"\n⚠ {fname}")
            print(f"  Issue: Ward field detected (conf:{conf:.3f}) but OCR text is empty")
        elif issue_type == 'CLEANING_FAILED':
            print(f"\n⚠ {fname}")
            print(f"  Raw text: '{text}'")
            print(f"  Confidence: {conf:.3f}")
            print(f"  Cleaning result: (empty)")

    # Attempt a full-image fallback OCR for missing/empty cases where original images exist
    print("\n" + "="*80)
    print("GLOBAL FALLBACK OCR ATTEMPT")
    print("="*80)
    for issue_type, filepath, text, conf in issues:
        if issue_type not in ('NOT_DETECTED', 'EMPTY_OCR'):
            continue
        # look for original back image in subfolder or uploads
        orig_back = None
        folder = os.path.splitext(filepath)[0]
        cand = os.path.join(folder, 'back_original.jpg')
        if os.path.exists(cand):
            orig_back = cand
        else:
            # maybe json lists back_image
            try:
                with open(filepath, encoding='utf-8') as f:
                    data = json.load(f)
                back_img_name = data.get('back_image')
                if back_img_name:
                    upath = os.path.join('uploads', back_img_name)
                    if os.path.exists(upath):
                        orig_back = upath
            except Exception:
                pass
        print(f"\n-- {os.path.basename(filepath)} --")
        if not orig_back:
            print("   No original back image available for fallback")
            continue
        try:
            img = Image.open(orig_back).convert('RGB')
            text_full = ocr_text(img, 'eng') + ' ' + ocr_text(img, 'nep')
            pattern = r"(?:ward|वडा|वर्ड)\s*(?:no(?:w|\.)?|number|नं|नंबर|न०)?\D*([०१२३४५६७८९0-9]{1,3})"
            m = re.search(pattern, text_full, flags=re.I)
            if m:
                ward_val = nepali_to_english_digits(m.group(1))
                print(f"   Fallback found '{ward_val}' from '{m.group(0)}'")
            else:
                print("   Fallback OCR could not locate a ward number")
        except Exception as e:
            print(f"   Fallback OCR error: {e}")

if __name__ == '__main__':
    diagnose_ward_extraction()
