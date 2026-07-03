#!/usr/bin/env python3
"""Test Tesseract directly on images"""
import pytesseract
from PIL import Image, ImageEnhance
import cv2
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

for filename in ['uploads/front3.jpg', 'uploads/back3.jpg']:
    print(f"\n{'=' * 60}")
    print(f"Testing pure Tesseract on: {filename}")
    print('=' * 60)
    
    # Load raw
    img_pil = Image.open(filename)
    print(f"Image size: {img_pil.size}, mode: {img_pil.mode}")
    
    # Test 1: Raw OCR
    print("\n1. Raw Tesseract:")
    text = pytesseract.image_to_string(img_pil, lang='eng')
    print(f"   Text length: {len(text)}")
    print(f"   Text: {text[:100] if text else '(empty)'}")
    
    # Test 2: Convert to greyscale
    print("\n2. Greyscale Tesseract:")
    img_gray = img_pil.convert('L')
    text = pytesseract.image_to_string(img_gray, lang='eng')
    print(f"   Text length: {len(text)}")
    print(f"   Text: {text[:100] if text else '(empty)'}")
    
    # Test 3: OpenCV preprocessing
    print("\n3. OpenCV threshold:")
    img_cv = cv2.imread(filename)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    img_thresh = Image.fromarray(thresh)
    text = pytesseract.image_to_string(img_thresh, lang='eng')
    print(f"   Text length: {len(text)}")
    print(f"   Text: {text[:100] if text else '(empty)'}")
    
    # Test 4: Enhance contrast
    print("\n4. Enhanced contrast:")
    img_enhanced = ImageEnhance.Contrast(img_pil).enhance(2.0)
    text = pytesseract.image_to_string(img_enhanced, lang='eng')
    print(f"   Text length: {len(text)}")
    print(f"   Text: {text[:100] if text else '(empty)'}")
