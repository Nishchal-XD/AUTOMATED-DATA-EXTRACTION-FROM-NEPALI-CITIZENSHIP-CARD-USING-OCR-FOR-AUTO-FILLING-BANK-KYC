#!/usr/bin/env python3
"""
Debug script to test individual components of the upload pipeline
"""
import os
import sys
from pathlib import Path

# Check critical paths and files
print("=" * 60)
print("NAGARIKTA UPLOAD SYSTEM DIAGNOSTICS")
print("=" * 60)

# 1. Check model file
print("\n[1] Checking YOLO Model...")
model_path = os.getenv("YOLO_MODEL_PATH", "weights/best.pt")
print(f"    Model path: {model_path}")
print(f"    Exists: {os.path.exists(model_path)}")
if os.path.exists(model_path):
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"    Size: {size_mb:.2f} MB")
else:
    print(f"    ❌ Model file NOT found!")

# 2. Check upload folder
print("\n[2] Checking Upload Folder...")
upload_folder = "uploads"
print(f"    Path: {upload_folder}")
print(f"    Exists: {os.path.exists(upload_folder)}")
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder, exist_ok=True)
    print(f"    ✓ Created")

# 3. Check dependencies
print("\n[3] Checking Python Dependencies...")
dependencies = {
    'flask': 'Flask web framework',
    'PIL': 'Image processing',
    'cv2': 'OpenCV',
    'numpy': 'Numerical computing',
    'pytesseract': 'OCR (Tesseract)',
    'easyocr': 'EasyOCR',
    'ultralytics': 'YOLO',
}

missing = []
for module, desc in dependencies.items():
    try:
        __import__(module)
        print(f"    ✓ {module:20} - {desc}")
    except ImportError:
        print(f"    ❌ {module:20} - {desc} [MISSING]")
        missing.append(module)

if missing:
    print(f"\n    Missing dependencies: {', '.join(missing)}")
    print(f"    Install with: pip install {' '.join(missing)}")

# 4. Check Tesseract
print("\n[4] Checking System Dependencies...")
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
print(f"    Tesseract: {tesseract_path}")
print(f"    Exists: {os.path.exists(tesseract_path)}")
if not os.path.exists(tesseract_path):
    print(f"    ❌ Tesseract NOT found at expected location")
    print(f"       Install from: https://github.com/UB-Mannheim/tesseract/wiki")

# 5. Try loading YOLO model
print("\n[5] Testing YOLO Model Loading...")
try:
    from ultralytics import YOLO
    print(f"    ✓ YOLO imported")
    
    if os.path.exists(model_path):
        print(f"    Loading model from {model_path}...")
        model = YOLO(model_path)
        print(f"    ✓ Model loaded successfully")
        print(f"    Model info: {model.model}")
    else:
        print(f"    ⚠ Cannot test model loading - file not found")
except Exception as e:
    print(f"    ❌ YOLO loading failed: {e}")
    import traceback
    traceback.print_exc()

# 6. Summary
print("\n" + "=" * 60)
print("DIAGNOSTIC SUMMARY")
print("=" * 60)

issues = []
if not os.path.exists(model_path):
    issues.append("YOLO model file not found")
if missing:
    issues.append(f"Missing Python dependencies: {', '.join(missing)}")
if not os.path.exists(tesseract_path):
    issues.append("Tesseract OCR not installed")

if issues:
    print("\n⚠️  ISSUES FOUND:\n")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    print("\nPlease fix these issues before running the application.")
else:
    print("\n✅ All systems appear operational!")
    print("\nTo start the application:")
    print("  python chatgpt.py")
    print("\nThen open browser to http://localhost:5001")

print("\n" + "=" * 60)
