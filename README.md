# Automated Data Extraction from Nepali Citizenship Card using OCR for Auto-Filling Bank KYC

An intelligent, end-to-end automation pipeline designed to extract structured textual information from images of Nepali Citizenship Cards (Nagarikta) using computer vision and Optical Character Recognition (OCR). The extracted data is parsed and formatted to seamlessly auto-fill banking Know Your Customer (KYC) systems, reducing manual data entry errors and onboarding friction.

---

## 🚀 Features
* **Document Alignment & Detection:** Uses a YOLO-based custom object detection model to locate and crop relevant zones of the citizenship document.
* **Multilingual OCR Engine:** Processes both English and Devanagari (Nepali) scripts to extract critical fields like Name, Date of Birth, Citizenship Number, Issue District, and Addresses.
* **Bank KYC Integration:** Provides a clean web interface built with Flask/FastAPI to simulate auto-filling a digital bank onboarding sheet.

---

## 🛠️ Tech Stack
* **Language:** Python
* **Computer Vision:** OpenCV, Ultralytics YOLOv8
* **OCR Engines:** Tesseract OCR / EasyOCR 
* **Backend Framework:** Flask / FastAPI
* **Frontend:** HTML5, CSS3, JavaScript (Bootstrap-based UI)

---

## 📂 Project Structure
```text
├── app.py                  # Main web application router
├── database.py             # Simulates saving the KYC form data
├── extraction_helpers.py   # Text cleanup algorithms and Regex parsers
├── data.yaml               # YOLO segmentation/bounding box configuration
├── static/                 # CSS, JavaScript, and asset files
├── templates/              # HTML frontend viewports (e.g., index.html)
└── requirements.txt        # Python package dependencies
