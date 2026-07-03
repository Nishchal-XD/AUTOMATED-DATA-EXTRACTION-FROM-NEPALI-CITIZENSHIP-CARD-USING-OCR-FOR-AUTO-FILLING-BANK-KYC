import os, glob, re
from main import model, preprocess_for_numbers, ocr_text, clean_field_text
from PIL import Image

cache_base = 'cache'

print('Re-running extraction on cached back images with fallback logic...')

for sub in sorted(os.listdir(cache_base)):
    subpath = os.path.join(cache_base, sub)
    if not os.path.isdir(subpath):
        continue
    back_img_path = os.path.join(subpath, 'back_original.jpg')
    if not os.path.exists(back_img_path):
        continue

    print(f'\n-- {sub} --')
    img = Image.open(back_img_path).convert('RGB')
    results = model.predict(source=[img], conf=0.5)
    res = results[0]
    boxes = getattr(res, 'boxes', None)
    boxes_list = boxes.data.tolist() if boxes is not None else []
    # select only ward boxes
    ward_boxes = []
    for box in boxes_list:
        cid = int(box[5]) if len(box) > 5 else 0
        if cid == 12:
            ward_boxes.append(box)
    if not ward_boxes:
        print('  No ward boxes detected by YOLO; running global text fallback')
        fulltext = ocr_text(img, 'eng') + ' ' + ocr_text(img, 'nep')
        m = re.search(r"ward\s*(?:no(?:w|\.)?|number)?\D*(\d{1,3})", fulltext, flags=re.I)
        if m:
            val = m.group(1)
            print(f'    fallback found ward {val} from "{m.group(0)}"')
        else:
            print('    fallback did not find any ward pattern')
    for i, box in enumerate(ward_boxes):
        x1, y1, x2, y2 = map(int, box[:4])
        crop_img = img.crop((x1, y1, x2, y2))
        width, height = crop_img.size
        if width < 150 or height < 50:
            scale_factor = max(2, 150 // width) if width > 0 else 2
            crop_img = crop_img.resize((width * scale_factor, height * scale_factor), Image.LANCZOS)
        crop = preprocess_for_numbers(crop_img)
        text = ocr_text(crop, 'eng', is_numeric=True)
        cleaned = clean_field_text(text, 12)
        print(f'  box {i}: raw="{text.strip()}" cleaned="{cleaned}"')
        if not cleaned:
            print('   > trying padded fallback')
            w,h = crop_img.size
            pad_w = max(5, w//10); pad_h = max(5, h//10)
            padded = Image.new('RGB', (w+2*pad_w, h+2*pad_h), (255,255,255))
            padded.paste(crop_img, (pad_w, pad_h))
            padded = preprocess_for_numbers(padded)
            text2 = ocr_text(padded, 'eng', is_numeric=True)
            cleaned2 = clean_field_text(text2, 12)
            print(f'      fallback raw="{text2.strip()}" cleaned="{cleaned2}"')
