import os
import glob
from PIL import Image
import pytesseract
from PIL import Image
import pytesseract
import numpy as np
import cv2
import os
from dotenv import load_dotenv
# load environment variables
dotenv_file = os.path.join(os.getcwd(), 'config.env')
if os.path.exists(dotenv_file):
    load_dotenv(dotenv_file)

# configure tesseract executable if provided
tesseract_path = os.getenv('TESSERACT_PATH')
if tesseract_path and os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# replicate needed helpers without importing main
TESS_CONFIG = "--oem 1 --psm 7"
TESS_CONFIG_NUMBERS = "--oem 1 --psm 8 -c tessedit_char_whitelist=0123456789"


def ocr_text(crop_image, tess_lang, is_numeric=False):
    config = TESS_CONFIG_NUMBERS if is_numeric else TESS_CONFIG
    return pytesseract.image_to_string(crop_image, lang=tess_lang, config=config)


def preprocess_for_numbers(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)
    denoised = cv2.bilateralFilter(contrast, 5, 50, 50)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    return Image.fromarray(dilated)


base = 'cache'

def process_crop(path):
    img = Image.open(path)
    # apply same preprocessing as main for ward number
    crop = preprocess_for_numbers(img)
    text_old = pytesseract.image_to_string(img, lang='eng', config="--oem 1 --psm 7")
    text_new = ocr_text(crop, 'eng', is_numeric=True)
    return text_old, text_new

for clip in glob.glob(os.path.join(base, '*')):
    if os.path.isdir(clip):
        json_path = os.path.join(clip, 'extracted_data.json')
        if not os.path.exists(json_path):
            continue
        print(f"\nDirectory: {clip}")
        crops = glob.glob(os.path.join(clip, 'crops', 'crop_back_class_12_*.png'))
        for c in crops:
            print(f"  Crop: {os.path.basename(c)}")
            old,new = process_crop(c)
            print(f"    old OCR: '{old.strip()}'")
            print(f"    new OCR: '{new.strip()}'")
