#!/usr/bin/env python3
"""Debug preprocessing on full image"""
from PIL import Image
import cv2
import numpy as np
from main import preprocess_image, deskew_image, preprocess_for_english
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img_path = 'uploads/back3.jpg'
img_pil = Image.open(img_path).convert("RGB")

print(f"Original image size: {img_pil.size}")

# Step 1: Try deskew
print("\n1. Testing deskew_image...")
try:
    deskewed = deskew_image(img_pil)
    print(f"   ✓ Deskewed successfully: {deskewed.size}")
    text = pytesseract.image_to_string(deskewed, lang='eng')
    print(f"   After deskew OCR: {len(text)} chars")
except Exception as e:
    print(f"   ✗ Deskew failed: {e}")
    deskewed = img_pil

# Step 2: Try preprocess_for_english
print("\n2. Testing preprocess_for_english...")
try:
    preprocessed = preprocess_for_english(deskewed)
    print(f"   ✓ Preprocessed: {preprocessed.size}")
    text = pytesseract.image_to_string(preprocessed, lang='eng')
    print(f"   After English preprocess OCR: {len(text)} chars")
    print(f"   Text: {text[:100]}")
except Exception as e:
    print(f"   ✗ English preprocess failed: {e}")

# Step 3: Try full preprocess_image pipeline
print("\n3. Testing preprocess_image pipeline...")
try:
    preprocessed = preprocess_image(img_pil, "eng")
    print(f"   ✓ Full pipeline: {preprocessed.size}")
    text = pytesseract.image_to_string(preprocessed, lang='eng')
    print(f"   After full pipeline OCR: {len(text)} chars")
    print(f"   Text: {text[:100]}")
except Exception as e:
    print(f"   ✗ Full pipeline failed: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Test on crop area (back of citizenship card typically has clearer text)
print("\n4. Testing on card middle crop (typical text area)...")
try:
    # typically text is in the middle/bottom of back of card
    h, w = img_pil.size[1], img_pil.size[0]
    crop = img_pil.crop((0, h//3, w, h))  # bottom 2/3
    print(f"   Crop size: {crop.size}")
    
    preprocessed = preprocess_image(crop, "eng")
    text = pytesseract.image_to_string(preprocessed, lang='eng')
    print(f"   Crop OCR: {len(text)} chars")
    print(f"   Text: {text[:100]}")
except Exception as e:
    print(f"   ✗ Crop test failed: {e}")
