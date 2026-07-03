from database import create_table, insert_kyc
from flask import Flask, request, jsonify, redirect, render_template, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
from flask_swagger_ui import get_swaggerui_blueprint
from ultralytics import YOLO
import os
import re
from PIL import Image
import pytesseract
import cv2
import numpy as np
from datetime import datetime
import json
import shutil
from pathlib import Path

try:
    import torch
    from transformers import NougatProcessor, VisionEncoderDecoderModel
except Exception:
    torch = None
    NougatProcessor = None
    VisionEncoderDecoderModel = None

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ------------------ CONFIG ------------------
SWAGGER_URL = '/api/docs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
TESS_CONFIG = "--oem 1 --psm 7"
UPLOAD_FOLDER = 'uploads'
CACHE_FOLDER = 'cache'  # New cache folder
OCR_BACKEND = os.getenv("OCR_BACKEND", "tesseract").lower()
NOUGAT_MODEL_ID = os.getenv("NOUGAT_MODEL_ID", "facebook/nougat-base")

# Class mapping to languages
placeholder = {
    0: "nep", 1: "nep", 2: "nep", 3: "nep",
    4: "eng", 5: "eng", 6: "eng", 7: "eng",
    8: "eng", 9: "eng", 10: "eng", 11: "eng",
    12: "eng", 13: "nep"
}

# ------------------ APP INIT ------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CACHE_FOLDER'] = CACHE_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)  # Create cache folder

# ------------------ CACHE FUNCTIONS ------------------
def get_session_cache_dir():
    """Create a unique cache directory for the current session"""
    session_id = session.get('session_id')
    if not session_id:
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S_') + str(os.urandom(4).hex())
        session['session_id'] = session_id
    
    cache_dir = os.path.join(app.config['CACHE_FOLDER'], session_id)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def save_extracted_data_to_cache(extracted_data, front_path, back_path):
    """Save all extracted data to cache folder"""
    try:
        cache_dir = get_session_cache_dir()
        
        # Save JSON data
        json_path = os.path.join(cache_dir, 'extracted_data.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
        # Copy original images to cache
        if front_path and os.path.exists(front_path):
            front_cache_path = os.path.join(cache_dir, 'front_original' + os.path.splitext(front_path)[1])
            shutil.copy2(front_path, front_cache_path)
            
        if back_path and os.path.exists(back_path):
            back_cache_path = os.path.join(cache_dir, 'back_original' + os.path.splitext(back_path)[1])
            shutil.copy2(back_path, back_cache_path)
        
        # Save timestamp
        timestamp_path = os.path.join(cache_dir, 'timestamp.txt')
        with open(timestamp_path, 'w') as f:
            f.write(datetime.now().isoformat())
        
        print(f"[DEBUG] Data saved to cache: {cache_dir}")
        return cache_dir
    except Exception as e:
        print(f"[ERROR] Failed to save to cache: {e}")
        return None

def save_crop_to_cache(crop_image, key, box_id, class_id):
    """Save individual crop images to cache"""
    try:
        cache_dir = get_session_cache_dir()
        crops_dir = os.path.join(cache_dir, 'crops')
        os.makedirs(crops_dir, exist_ok=True)
        
        crop_filename = f"crop_{key}_class_{class_id}_box_{box_id}.png"
        crop_path = os.path.join(crops_dir, crop_filename)
        crop_image.save(crop_path)
        return crop_path
    except Exception as e:
        print(f"[ERROR] Failed to save crop to cache: {e}")
        return None

def get_cached_data(session_id=None):
    """Retrieve cached data for a session"""
    try:
        if session_id:
            cache_dir = os.path.join(app.config['CACHE_FOLDER'], session_id)
        else:
            cache_dir = get_session_cache_dir()
        
        json_path = os.path.join(cache_dir, 'extracted_data.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read cache: {e}")
    return None

# ------------------ MODEL ------------------
model = None
nougat_processor = None
nougat_model = None
nougat_device = "cpu"

def get_model():
    global model
    if model is None:
        # Use actual path to your model
        model_path = r"C:\nagarikta\weights\best.pt"
        print(f"[DEBUG] Loading YOLO model from: {model_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        model = YOLO(model_path)
        print("[DEBUG] Model loaded successfully")
    return model

def get_nougat():
    global nougat_processor, nougat_model, nougat_device
    if nougat_processor is None or nougat_model is None:
        if NougatProcessor is None or VisionEncoderDecoderModel is None or torch is None:
            raise RuntimeError("Nougat dependencies are missing. Install torch and transformers.")
        nougat_device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[DEBUG] Loading Nougat model ({NOUGAT_MODEL_ID}) on {nougat_device}")
        nougat_processor = NougatProcessor.from_pretrained(NOUGAT_MODEL_ID)
        nougat_model = VisionEncoderDecoderModel.from_pretrained(NOUGAT_MODEL_ID).to(nougat_device)
        nougat_model.eval()
    return nougat_processor, nougat_model, nougat_device

def ocr_with_nougat(pil_img):
    processor, model, device = get_nougat()
    pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values.to(device)
    with torch.no_grad():
        outputs = model.generate(
            pixel_values,
            max_new_tokens=128,
            bad_words_ids=[[processor.tokenizer.unk_token_id]],
        )
    text = processor.batch_decode(outputs, skip_special_tokens=True)[0]
    return normalize_ocr_text(text)

def ocr_text(crop_image, tess_lang):
    if OCR_BACKEND == "nougat":
        try:
            return ocr_with_nougat(crop_image)
        except Exception as e:
            print(f"[WARN] Nougat OCR failed, falling back to Tesseract: {e}")
    return pytesseract.image_to_string(crop_image, lang=tess_lang, config=TESS_CONFIG)

def safe_json(obj):
    if isinstance(obj, dict):
        return {str(k): safe_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json(i) for i in obj]
    elif isinstance(obj, (int, float, str)):
        return obj
    elif obj is None:
        return ""
    else:
        return str(obj)

# ------------------ SWAGGER ------------------
try:
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        '/static/swagger.yaml',
        config={'app_name': "My Flask API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
except Exception as e:
    print("[ERROR] Swagger init error:", e)

# ------------------ HELPERS ------------------
def allowed_file(*filenames):
    for fname in filenames:
        if '.' not in fname or fname.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
            return False
    return True

def preprocess_for_nepali(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return Image.fromarray(thresh)

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text

def strip_generic_leading_label(text):
    # Generic fallback: convert "Label ... : value" into "value".
    # Handles both English and Devanagari labels (e.g., "नाम धर: ...").
    match = re.match(r"^\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{1,40})\s*[:._\-]+\s*(.+)$", text)
    if match:
        return match.group(2).strip()
    return text

def clean_perm_district(text):
    text = normalize_ocr_text(text)
    text = re.sub(r"(?i)^district\s*[:\-–—.]*\s*", "", text).strip()
    # Keep only letters/spaces for district names like LALITPUR
    text = re.sub(r"[^A-Za-z\s]", "", text).strip()
    return text

def clean_perm_address(text):
    text = normalize_ocr_text(text)
    text = re.sub(r"(?i)^permanent\s*address\s*[:\-–—.]*\s*", "", text).strip()
    # Remove any district part accidentally included in the same crop.
    text = re.sub(r"(?i)\s*[–—-]?\s*district\s*:\s*.*$", "", text).strip()
    # Remove punctuation-only leftovers such as ".-."
    text = re.sub(r"^[^\w]+|[^\w]+$", "", text).strip()
    return text

# Label variants commonly seen in OCR before actual values.
FIELD_PREFIX_PATTERNS = {
    0: [r"issued\s*office", r"office"],
    1: [r"name", r"full\s*name"],
    2: [r"(?:father\s*'?s?)\s*name"],
    3: [r"(?:mother\s*'?s?)\s*name"],
    4: [r"citizenship\s*(?:no|number)"],
    5: [r"full\s*name", r"name"],
    6: [r"sex", r"gender"],
    7: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*year", r"birth\s*year", r"year"],
    8: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*month", r"birth\s*month", r"month"],
    9: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*day", r"birth\s*day", r"day"],
    10: [r"permanent\s*district", r"district"],
    11: [r"permanent\s*address", r"address"],
    12: [r"ward\s*(?:no|number)"],
    13: [r"issued\s*date", r"date\s*of\s*issue", r"issue\s*date"],
}

def strip_field_prefix(text, class_id):
    patterns = FIELD_PREFIX_PATTERNS.get(class_id, [])
    for base in patterns:
        text = re.sub(
            rf"(?i)^\s*{base}\s*[:.\-–—_]*\s*",
            "",
            text,
            count=1
        )
    return text

def clean_field_text(text, class_id):
    text = normalize_ocr_text(text)
    if class_id == 10:
        return clean_perm_district(text)
    if class_id == 11:
        return clean_perm_address(text)
    text = strip_field_prefix(text, class_id)
    text = strip_generic_leading_label(text)
    text = re.sub(r"^[\W_]+", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"[\W_]+$", "", text, flags=re.UNICODE).strip()
    return text

def parse_to_html_date(date_text):
    date_text = normalize_ocr_text(date_text)
    if not date_text:
        return ""

    # Keep digits and common separators for robust parsing.
    normalized = re.sub(r"[^\d/\-.]", "", date_text)
    normalized = normalized.strip(" /-.")
    if not normalized:
        return ""

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(normalized, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""

# ------------------ ROUTES ------------------
@app.route("/", methods=['GET'])
def index():
    try:
        return send_from_directory('static', 'index.html')
    except Exception as e:
        print("[ERROR] Serving index.html:", e)
        return "Internal Server Error", 500

@app.route("/api/upload", methods=['POST'])
def upload_file():
    try:    
        if 'front' not in request.files or 'back' not in request.files:
            return "Both files are required", 400

        front_file = request.files['front']
        back_file = request.files['back']

        if not front_file.filename or not back_file.filename:
            return "Empty filename detected", 400
        if not allowed_file(front_file.filename, back_file.filename):
            return "Invalid file extension", 400

        # Save uploaded files
        front_name = secure_filename(front_file.filename)
        back_name = secure_filename(back_file.filename)
        front_path = os.path.join(app.config['UPLOAD_FOLDER'], front_name)
        back_path = os.path.join(app.config['UPLOAD_FOLDER'], back_name)
        front_file.save(front_path)
        back_file.save(back_path)
        print(f"[DEBUG] Saved front image: {front_path}")
        print(f"[DEBUG] Saved back image: {back_path}")

        # Load images
        front_img = Image.open(front_path).convert("RGB")
        back_img = Image.open(back_path).convert("RGB")

        # YOLO prediction
        model = get_model()
        results = model.predict(source=[front_img, back_img], conf=0.5)
        print("[DEBUG] YOLO prediction completed")

        final_output = {"front": [], "back": []}
        all_crops_data = {"front": [], "back": []}

        for key, res, img in zip(["front", "back"], results, [front_img, back_img]):
            boxes = getattr(res, 'boxes', None)
            boxes_list = boxes.data.tolist() if boxes is not None else []

            for i, box in enumerate(boxes_list):
                try:
                    x1, y1, x2, y2 = map(int, box[:4])
                    conf = float(box[4]) if len(box) > 4 else 0.0
                    class_id = int(box[5]) if len(box) > 5 else 0
                except Exception as e:
                    print("[ERROR] Box parsing error:", e, "box:", box)
                    continue

                # Determine OCR language
                lang = placeholder.get(class_id, "eng")
                tess_lang = "nep" if lang == "nep" else "eng"

                # Crop and preprocess
                crop_img = img.crop((x1, y1, x2, y2))
                crop = preprocess_for_nepali(crop_img) if tess_lang == "nep" else crop_img

                # Save crop image to cache
                crop_path = save_crop_to_cache(crop, key, i, class_id)
                
                # Save crop to uploads folder (keep original behavior)
                upload_crop_path = os.path.join(app.config['UPLOAD_FOLDER'], f"crop_{key}_{i}.png")
                try:
                    crop.save(upload_crop_path)
                except Exception as e:
                    print("[ERROR] Failed to save crop:", e, "path:", upload_crop_path)

                # OCR text
                text = ocr_text(crop, tess_lang)
                cleaned_text = clean_field_text(text, class_id)

                crop_data = {
                    "box_id": i,
                    "class_id": class_id,
                    "confidence": conf if np.isfinite(conf) else 0.0,
                    "text": cleaned_text,
                    "crop_path": crop_path,
                    "coordinates": [x1, y1, x2, y2]
                }
                
                final_output[key].append(crop_data)
                all_crops_data[key].append(crop_data)

        # validate by comparing nagrikta numbers only
        def _nagrikta_number(field_list):
            for item in field_list:
                txt = item.get("text", "")
                if not txt:
                    continue
                txt = nepali_to_english_digits(txt)
                num = re.sub(r"\D", "", txt)
                if len(num) >= 4:
                    return num
            return ""

        front_num = _nagrikta_number(final_output.get("front", []))
        back_num = _nagrikta_number(final_output.get("back", []))
        print(f"[DEBUG] nagrikta front={front_num!r} back={back_num!r}")
        if not front_num or not back_num:
            return "Unable to verify nagrikta number on one or both pages", 400
        if front_num != back_num:
            return "Nagrikta numbers do not match", 400

        # Prepare complete extracted data for cache
        extracted_data = {
            "timestamp": datetime.now().isoformat(),
            "front_image": front_name,
            "back_image": back_name,
            "extracted_fields": final_output,
            "crops": all_crops_data,
            "metadata": {
                "ocr_backend": OCR_BACKEND,
                "model_confidence": 0.5,
                "total_fields_extracted": len(final_output["front"]) + len(final_output["back"])
            }
        }

        # Save all extracted data to cache
        cache_dir = save_extracted_data_to_cache(extracted_data, front_path, back_path)
        
        # Store cache info in session
        session['kyc_data'] = final_output
        session['front_file'] = front_name
        session['back_file'] = back_name
        session['cache_dir'] = cache_dir

        print("[DEBUG] Final OCR Output:", safe_json(final_output))
        print(f"[DEBUG] Data cached at: {cache_dir}")

        kyc_url = url_for('kyc_form')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'redirect': kyc_url}), 200

        return redirect(kyc_url)

    except Exception as e:
        print("[ERROR] Upload processing error:", e)
        return f"Error: {e}", 500

@app.route("/kycform", methods=['GET'])
def kyc_form():
    kyc_data = session.get('kyc_data', {"front": [], "back": []})
    front_file = session.get('front_file', '')
    back_file = session.get('back_file', '')
    cache_dir = session.get('cache_dir', '')

    def get_text(data_list, class_id):
        for item in data_list:
            if item.get("class_id") == class_id and item.get("text"):
                return item["text"]
        return ""

    dob_year = get_text(kyc_data.get("back", []), 7)
    dob_month = get_text(kyc_data.get("back", []), 8)
    dob_day = get_text(kyc_data.get("back", []), 9)
    dob = ""
    if dob_year and dob_month and dob_day:
        try:
            dob = datetime(
                int(re.sub(r"\D", "", dob_year)),
                int(re.sub(r"\D", "", dob_month)),
                int(re.sub(r"\D", "", dob_day)),
            ).strftime("%Y-%m-%d")
        except ValueError:
            dob = ""

    prefill = {
        "branch": get_text(kyc_data.get("front", []), 0),
        "fullname": get_text(kyc_data.get("back", []), 5),
        "nepname": get_text(kyc_data.get("front", []), 1),
        "father_name": get_text(kyc_data.get("front", []), 2),
        "mother_name": get_text(kyc_data.get("front", []), 3),
        "docnum": get_text(kyc_data.get("back", []), 4),
        "gender": get_text(kyc_data.get("back", []), 6),
        "dob_year": dob_year,
        "dob_month": dob_month,
        "dob_day": dob_day,
        "dob": dob,
        "issuedate": parse_to_html_date(get_text(kyc_data.get("back", []), 13)),
        "nationality": "Nepali",
        "district": get_text(kyc_data.get("back", []), 10),
        "address": get_text(kyc_data.get("back", []), 11),
        "ward_no": get_text(kyc_data.get("back", []), 12),
    }

    return render_template(
        "kycform.html",
        front=front_file,
        back=back_file,
        prefill=prefill,
        cache_dir=cache_dir
    )

# New endpoint to view cached data
@app.route("/api/cache/<session_id>", methods=['GET'])
def view_cached_data(session_id):
    """Endpoint to view cached data for a specific session"""
    try:
        cached_data = get_cached_data(session_id)
        if cached_data:
            return jsonify(cached_data)
        else:
            return jsonify({"error": "Cache not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New endpoint to list all cache sessions
@app.route("/api/cache/list", methods=['GET'])
def list_cache_sessions():
    """List all cached sessions"""
    try:
        cache_dir = app.config['CACHE_FOLDER']
        sessions = []
        
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            if os.path.isdir(item_path):
                json_path = os.path.join(item_path, 'extracted_data.json')
                timestamp_path = os.path.join(item_path, 'timestamp.txt')
                
                session_info = {
                    "session_id": item,
                    "path": item_path,
                    "has_data": os.path.exists(json_path),
                    "timestamp": None
                }
                
                if os.path.exists(timestamp_path):
                    with open(timestamp_path, 'r') as f:
                        session_info["timestamp"] = f.read()
                
                sessions.append(session_info)
        
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------ MAIN ------------------
if __name__ == '__main__':
    try:
        # Create database table
        create_table()
        print("[DEBUG] Database table created/verified")
        
        app.run(debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        print("[ERROR] App failed to start:", e)