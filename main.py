import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

from database import create_table, insert_kyc
from flask import Flask, request, jsonify, redirect, render_template, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
from flask_swagger_ui import get_swaggerui_blueprint 
from ultralytics import YOLO
import re
from PIL import Image
import pytesseract
import cv2
import numpy as np
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


try:
    import torch
    from transformers import NougatProcessor, VisionEncoderDecoderModel
except Exception:
    torch = None
    NougatProcessor = None
    VisionEncoderDecoderModel = None

tesseract_path = os.getenv('TESSERACT_PATH')
if tesseract_path and os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path 

# ------------------ CONFIG ------------------
SWAGGER_URL = '/api/docs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
TESS_CONFIG_ENG = "--oem 1 --psm 7"
TESS_CONFIG_NEP = "--oem 1 --psm 7"
UPLOAD_FOLDER = 'uploads'
OCR_BACKEND = os.getenv("OCR_BACKEND", "tesseract").lower()
NOUGAT_MODEL_ID = os.getenv("NOUGAT_MODEL_ID", "facebook/nougat-base")

# Class mapping to languages
placeholder = {
    0: "nep", 1: "nep", 2: "nep", 3: "nep",
    4: "eng", 5: "eng", 6: "eng", 7: "eng",
    8: "eng", 9: "eng", 10: "eng", 11: "eng",
    12: "eng", 13: "nep"
}

# Complete list of all 77 districts of Nepal
NEPAL_DISTRICTS = [
    "Achham", "Arghakhanchi", "Baglung", "Baitadi", "Bajhang", "Bajura", 
    "Banke", "Bara", "Bardiya", "Bhaktapur", "Bhojpur", "Chitwan", 
    "Dadeldhura", "Dailekh", "Dang", "Darchula", "Dhading", "Dhankuta", 
    "Dhanusha", "Dholkha", "Dolpa", "Doti", "Gorkha", "Gulmi", 
    "Humla", "Ilam", "Jajarkot", "Jhapa", "Jumla", "Kailali", 
    "Kalikot", "Kanchanpur", "Kapilvastu", "Kaski", "Kathmandu", 
    "Kavrepalanchok", "Khotang", "Lalitpur", "Lamjung", "Mahottari", 
    "Makwanpur", "Manang", "Morang", "Mugu", "Mustang", "Myagdi", 
    "Nawalparasi", "Nuwakot", "Okhaldhunga", "Palpa", "Panchthar", 
    "Parbat", "Parsa", "Pyuthan", "Ramechhap", "Rasuwa", "Rautahat", 
    "Rolpa", "Rukum", "Rupandehi", "Salyan", "Sankhuwasabha", 
    "Saptari", "Sarlahi", "Sindhuli", "Sindhupalchok", "Siraha", 
    "Solukhumbu", "Sunsari", "Surkhet", "Syangja", "Tanahun", 
    "Taplejung", "Tehrathum", "Udayapur"
]

# Complete list of all Municipalities and Rural Municipalities of Nepal
NEPAL_MUNICIPALITIES = {
    # Province 1
    "taplejung": ["Phungling", "Maiwa Khola", "Meringden", "Mikwakhola", "Phaktanglung", "Sidingba", "Pathibhara", "Sirijanga"],
    "panchthar": ["Phidim", "Falelung", "Falgunanda", "Hilihang", "Kummayak", "Tumbewa", "Yangwarak"],
    "ilam": ["Ilam", "Deumai", "Mai", "Suryodaya", "Fakphokthum", "Mangsebung", "Chulachuli", "Rong", "Sandakpur"],
    "jhapa": ["Mechinagar", "Bhadrapur", "Birtamod", "Arjundhara", "Kankai", "Gauradaha", "Damak", "Gauriganj", "Buddhashanti", "Haldibari", "Barhadashi", "Jhapa", "Shivasatakshi", "Kamal"],
    "morang": ["Biratnagar", "Belbari", "Letang", "Pathari Sanischare", "Rangeli", "Ratuwamai", "Sunawarshi", "Uralabari", "Budi Ganga", "Dhanpalthan", "Gramthan", "Jahada", "Kanepokhari", "Katahari", "Kerabari", "Miklajung"],
    "sunsari": ["Itahari", "Dharan", "Inaruwa", "Duhabi", "Ramdhuni", "Barahachhetra", "Dewanganj", "Koshi", "Gadhi", "Barju", "Bhokraha", "Harinagara"],
    
    # Province 2
    "saptari": ["Rajbiraj", "Kanchanrup", "Dakneshwori", "Bode Barsain", "Khadak", "Shambhunath", "Surunga", "Hanumannagar", "Balan Bihul", "Bishnupur", "Chhinnamasta", "Mahadeva", "Rupani", "Tirahut", "Tilathi", "Agnisair", "Rajgadh"],
    "siraha": ["Lahan", "Dhangadhimai", "Siraha", "Golbazar", "Mirchaiya", "Kalyanpur", "Karjanha", "Sukhipur", "Bhagwanpur", "Aurahi", "Bariyarpatti", "Laxmipur Patari", "Naraha", "Sakhuwanankarkatti", "Arnama"],
    "dhanusha": ["Janakpur", "Dhanushadham", "Mithila", "Sabaila", "Hansapur", "Shahidnagar", "Kamala", "Mithila Bihari", "Bateshwar", "Lakshminiya", "Aurahi", "Bideha", "Ganeshman", "Dhanauji"],
    "mahottari": ["Jaleshwar", "Bardibas", "Gaushala", "Loharpatti", "Ramgopalpur", "Aurahi", "Balawa", "Ekdara", "Mahottari", "Manra Siswa", "Matihani", "Pipra", "Samsi", "Sonama"],
    "sarlahi": ["Malangwa", "Ishworpur", "Haripur", "Haripurwa", "Hariwan", "Barahathawa", "Balara", "Kaudena", "Chakraghatta", "Chandranagar", "Dhankaul", "Parsa", "Basbaria", "Bramhapuri", "Ramnagar", "Rajghat"],
    "bara": ["Kalaiya", "Jitpur Simara", "Kolhabi", "Nijgadh", "Mahagadhimai", "Simraungadh", "Pacharauta", "Prasauni", "Bishrampur", "Devtal", "Karaiyamai", "Baragadhi", "Pheta", "Adarsh Kotwal"],
    "parsa": ["Birgunj", "Bahudarmai", "Parsagadhi", "Pokhariya", "Bindabasini", "Chhipaharmai", "Jagarnathpur", "Jirabhawani", "Kalikamai", "Pakaha Mainpur", "Paterwa Sugauli", "Sakhuwa Prasauni", "Thori"],
    "rautahat": ["Gaur", "Baudhimai", "Brindaban", "Chandrapur", "Dewahi Gonahi", "Garuda", "Gujara", "Ishanath", "Katahariya", "Madhav Narayan", "Maulapur", "Paroha", "Phatuwa Bijayapur", "Rajdevi", "Rajpur", "Yamunamai"],
    
    # Bagmati Province
    "sindhuli": ["Kamalamai", "Dudhauli", "Sunkoshi", "Hariharpur", "Tinpatan", "Marin", "Golanjor", "Phikkal"],
    "ramechhap": ["Manthali", "Ramechhap", "Umakunda", "Khandadevi", "Doramba", "Gokulganga", "Likhu"],
    "dolakha": ["Bhimeshwar", "Jiri", "Kalinchok", "Melung", "Bigu", "Gaurishankar", "Baiteshwar", "Shailung", "Tamakoshi"],
    "bhaktapur": ["Bhaktapur", "Madhyapur Thimi", "Changunarayan", "Suryabinayak"],
    "lalitpur": ["Lalitpur", "Godawari", "Mahalaxmi", "Bagmati", "Konjyosom", "Mahankal"],
    "kathmandu": ["Kathmandu", "Kirtipur", "Gokarneshwar", "Chandragiri", "Tokha", "Tarkeshwar", "Dakshinkali", "Nagarjun", "Budhanilkantha", "Shankharapur"],
    "kavrepalanchok": ["Dhulikhel", "Banepa", "Panauti", "Panchkhal", "Namobuddha", "Mandan Deupur", "Bhumi", "Khanikhola", "Mahabharat", "Roshi", "Temal", "Chaunri Deurali"],
    "nuwakot": ["Bidur", "Belkotgadhi", "Kakani", "Panchakanya", "Likhu", "Dupcheshwar", "Shivapuri", "Tadi", "Suryagadhi", "Tarkeshwar", "Kispang", "Myagang"],
    "rasuwa": ["Dhunche", "Gosaikunda", "Aamachhodingmo", "Uttargaya", "Kalika"],
    "dhading": ["Nilkantha", "Dhunibeshi", "Gajuri", "Galchhi", "Gangajamuna", "Jwalamukhi", "Thakre", "Netrawati", "Benighat Rorang", "Rubi Valley", "Siddhalek", "Tripura Sundari", "Khaniyabash"],
    "makwanpur": ["Hetauda", "Thaha", "Bhimphedi", "Makawanpurgadhi", "Manahari", "Bakaiya", "Bagmati", "Raksirang", "Indrasarowar", "Kailash"],
    "chitwan": ["Bharatpur", "Ratnanagar", "Khairhani", "Kalika", "Rapti", "Madi", "Ichchhakamana"],
    
    # Gandaki Province
    "gorkha": ["Gorkha", "Palungtar", "Sulikot", "Siranchowk", "Ajirkot", "Chumanubri", "Dharche", "Barpak", "Shahid Lakhan"],
    "lamjung": ["Besisahar", "Madhya Nepal", "Rainas", "Sundarbazar", "Dordi", "Marsyangdi", "Kwholasothar", "Dudhpokhari"],
    "tanahun": ["Byas", "Shuklagandaki", "Bhimad", "Bandipur", "Devghat", "Anbu Khaireni", "Rishing", "Ghiring", "Myagde"],
    "kaski": ["Pokhara", "Annapurna", "Machhapuchchhre", "Madi", "Rupa"],
    "manang": ["Chame", "Narshon", "Narpa Bhumi", "Manang Ngisyang"],
    "mustang": ["Jomsom", "Kagbeni", "Thasang", "Lomanthang", "Lo-The", "Dalome", "Gharapjhong", "Baragung Muktichhetra"],
    "myagdi": ["Beni", "Annapurna", "Dhawalagiri", "Raghuganga", "Malika", "Mangala"],
    "parbat": ["Kusma", "Phalewas", "Jaljala", "Paiyun", "Mahashila", "Modi", "Bihadi"],
    "baglung": ["Baglung", "Galkot", "Jaimuni", "Dhorpatan", "Bareng", "Kanthekhola", "Taman", "Tara Khola", "Nisi Khola"],
    "syangja": ["Putalibazar", "Waling", "Galyang", "Chapakot", "Bhirkot", "Biruwa", "Harinas", "Kaligandaki", "Phedikhola", "Aandhikhola"],
    "nawalpur": ["Kawasoti", "Gaindakot", "Devchuli", "Madhyabindu", "Bungdikali", "Bulingtar", "Hupsekot"],
    
    # Lumbini Province
    "rupandehi": ["Butwal", "Siddharthanagar", "Lumbini Sanskritik", "Sainamaina", "Devdaha", "Tillotama", "Siyari", "Gaidahawa", "Mayadevi", "Kotahimai", "Marchawari", "Rohini", "Sammarimai", "Omsatiya", "Kanchan"],
    "kapilvastu": ["Kapilvastu", "Banganga", "Buddhabhumi", "Shivaraj", "Krishnanagar", "Maharajganj", "Mayadevi", "Yasodhara", "Suddhodhan", "Bidya"],
    "palpa": ["Tansen", "Rampur", "Purbakhola", "Bagnaskali", "Ribdikot", "Rambha", "Mathagadhi", "Nisdi", "Tinau", "Raina"],
    "arghakhanchi": ["Sandhikharka", "Sitganga", "Bhumekasthan", "Chhatradev", "Panini", "Malarani"],
    "gulmi": ["Musikot", "Ruru", "Resunga", "Chhatrakot", "Gulmi", "Kali Gandaki", "Madane", "Malika", "Dhurkot", "Satyawati", "Limgha"],
    "pyuthan": ["Pyuthan", "Sworgadwari", "Gaumukhi", "Mandavi", "Sarumarani", "Mallarani", "Nau Bahini", "Jhimruk", "Ayirawati"],
    "rolpa": ["Rolpa", "Runtigadhi", "Triveni", "Sunil Smriti", "Lungri", "Sukidaha", "Thawang", "Madi", "Ganga Dev", "Pariwartan"],
    "rukum_east": ["Putha Uttarganga", "Bhume", "Sisne"],
    "dang": ["Ghorahi", "Tulsipur", "Lamahi", "Bangalachuli", "Dangisharan", "Gadhawa", "Rajpur", "Shantinagar", "Rapti", "Babai"],
    "banke": ["Nepalgunj", "Kohalpur", "Khajura", "Janaki", "Duduwa", "Narainapur", "Rapti Sonari", "Baijanath"],
    "bardiya": ["Gulariya", "Rajapur", "Madhuwan", "Thakurbaba", "Basgadhi", "Barbardiya", "Badhaiyatal", "Geruwa"],
    
    # Karnali Province
    "rukum_west": ["Musikot", "Chaurjahari", "Aathbiskot", "Banphikot", "Triveni", "Sanibheri"],
    "salyan": ["Salyan", "Sharada", "Bagchaur", "Bangad Kupinde", "Kalimati", "Triveni", "Kumakh", "Darma"],
    "dolpa": ["Thuli Bheri", "Tripura Sundari", "Dolpo Buddha", "She Phoksundo", "Jagadulla", "Mudkechula", "Kaike", "Chharka Tangsong"],
    "jumla": ["Chandannath", "Kankasundari", "Sinja", "Hima", "Tila", "Guthichaur", "Tatopani", "Patarasi"],
    "mugu": ["Chhayanath Rara", "Mugum Karmarong", "Soru", "Khatyad"],
    "humla": ["Simkot", "Sarkegad", "Adanchuli", "Kharpunath", "Tanjakot", "Chankheli", "Namkha"],
    "kalikot": ["Manma", "Khandachakra", "Raskot", "Tilagufa", "Narharinath", "Pachaljharana", "Sanni Triveni", "Mahawai", "Palata"],
    "dailekh": ["Narayan", "Dullu", "Aathabis", "Chamunda Bindrasaini", "Thantikandh", "Bhagawatimai", "Gurans", "Dungeshwar", "Naumule", "Mahabu"],
    "jajarkot": ["Bheri", "Chhedagad", "Nalgad", "Junichande", "Kushe", "Barekot", "Shivalaya"],
    
    # Sudurpashchim Province
    "bajura": ["Budhinanda", "Budhiganga", "Tribeni", "Jagannath", "Swami Kartik", "Chhededha", "Himali", "Gaumul", "Khaptad Chhededha"],
    "bajhang": ["Jaya Prithvi", "Bungal", "Talkot", "Masta", "Khaptadchhanna", "Thalara", "Bitthadchir", "Surma", "Chhabis Pathibhara", "Durgathali", "Kedarsyu", "Sai"],
    "doti": ["Dipayal Silgadhi", "Shikhar", "Purbichauki", "Badikedar", "Jorayal", "Sayal", "Aadarsha", "K.I. Singh", "Bogatan"],
    "achham": ["Mangalsen", "Kamalbazar", "Sanfebagar", "Panchadewal Binayak", "Chaurpati", "Mellekh", "Bannigadi Jayagad", "Ramaroshan", "Dhakari", "Turmakhand"],
    "darchula": ["Mahakali", "Shailyashikhar", "Malikarjun", "Apihimal", "Duhun", "Lekam", "Marma", "Naugad", "Sitad", "Byas"],
    "baitadi": ["Dasharathchand", "Patan", "Melauli", "Purchaudi", "Sunarya", "Sigas", "Shivanath", "Surnaya", "Dilasaini", "Dogdakedar", "Pancheshwar"],
    "dadeldhura": ["Amargadhi", "Parshuram", "Aalitaal", "Bhageshwar", "Nawadurga", "Ajaymeru", "Ganyapadhura"],
    "kanchanpur": ["Bhimdatta", "Bedkot", "Mahakali", "Laljhadi", "Punarbas", "Dodhara Chandani", "Krishnapur", "Beldandi", "Suklaphanta"],
    "kailali": ["Dhangadhi", "Tikapur", "Ghodaghodi", "Lamkichuha", "Bhajani", "Godawari", "Gauriganga", "Janaki", "Bardagoriya", "Mohanyal", "Kailari", "Joshipur", "Chure"],
}

# Flatten the list for easy lookup (case-insensitive)
ALL_MUNICIPALITIES = []
MUNICIPALITY_MAPPING = {}

for district, muns in NEPAL_MUNICIPALITIES.items():
    for mun in muns:
        ALL_MUNICIPALITIES.append(mun)
        # Add variations
        MUNICIPALITY_MAPPING[mun.lower()] = mun
        MUNICIPALITY_MAPPING[mun.lower().replace(" ", "")] = mun
        MUNICIPALITY_MAPPING[mun.upper()] = mun

# Common OCR variations
OCR_VARIATIONS = {
    # Kanchanpur
    "rm beldandi": "Beldandi",
    "r m beldandi": "Beldandi",
    "r.m. beldandi": "Beldandi",
    "beldandi": "Beldandi",
    "beldaandi": "Beldandi",
    "beldangi": "Beldandi",
    "bhimdatta": "Bhimdatta",
    "bedkot": "Bedkot",
    "krishnapur": "Krishnapur",
    
    # Banke
    "kohalpur": "Kohalpur",
    "kohalpur municipality": "Kohalpur",
    "nepalgunj": "Nepalgunj",
    "khajura": "Khajura",
    "janaki": "Janaki",
    "baijanath": "Baijanath",
    
    # Bhaktapur
    "bhaktapur": "Bhaktapur",
    "madhyapur thimi": "Madhyapur Thimi",
    "changunarayan": "Changunarayan",
    "suryabinayak": "Suryabinayak",
    
    # Gulmi
    "satyawati": "Satyawati",
    "satyawati rm": "Satyawati",
    "limgha": "Limgha",
    "musikot": "Musikot",
    "resunga": "Resunga",
    "dhurkot": "Dhurkot",
    "malika": "Malika",
    
    # Sarlahi
    "rajghat": "Rajghat",
    "malangwa": "Malangwa",
    "ishworpur": "Ishworpur",
    "haripur": "Haripur",
    "haripurwa": "Haripurwa",
    "hariwan": "Hariwan",
    "barahathawa": "Barahathawa",
    
    # Lalitpur
    "lalitpur": "Lalitpur",
    "godawari": "Godawari",
    "mahalaxmi": "Mahalaxmi",
    
    # Kathmandu
    "kathmandu": "Kathmandu",
    "kirtipur": "Kirtipur",
    "nagarjun": "Nagarjun",
    
    # Tanahun
    "vyas": "Byas",
    "vyas municipality": "Byas",
    "municipality vyas": "Byas",
}

# Add all variations to mapping
for var, correct in OCR_VARIATIONS.items():
    MUNICIPALITY_MAPPING[var] = correct
    MUNICIPALITY_MAPPING[var.lower()] = correct
    MUNICIPALITY_MAPPING[var.replace(" ", "")] = correct

def correct_municipality_name(ocr_text, district_name=None):
    """Match OCR text to correct Nepal municipality name"""
    if not ocr_text:
        return ocr_text
    
    # Clean the input
    cleaned = str(ocr_text).strip().lower()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # First check direct match in our mapping
    if cleaned in MUNICIPALITY_MAPPING:
        return MUNICIPALITY_MAPPING[cleaned]
    
    # Check if it's in the list of all municipalities (case-insensitive)
    for mun in ALL_MUNICIPALITIES:
        if mun.lower() == cleaned:
            return mun
        if mun.lower() in cleaned or cleaned in mun.lower():
            return mun
    
    # If district is known, prioritize that district's municipalities
    if district_name and district_name.lower() in NEPAL_MUNICIPALITIES:
        district_muns = NEPAL_MUNICIPALITIES[district_name.lower()]
        for mun in district_muns:
            if mun.lower() in cleaned or cleaned in mun.lower():
                return mun
    
    # Handle "R M Something" pattern
    if cleaned.startswith(('rm ', 'r.m.', 'r m')):
        # Extract the name part
        name_part = re.sub(r'^(rm|r\.m\.|r m)\s+', '', cleaned)
        name_part = name_part.strip()
        
        # Look for this name in all municipalities
        for mun in ALL_MUNICIPALITIES:
            if name_part in mun.lower() or mun.lower() in name_part:
                return mun
        
        # If still not found, capitalize it properly
        return name_part.title()
    
    # If no match found, return cleaned and capitalized
    return cleaned.title()

def correct_district_name(ocr_text):
    """Match OCR text to correct Nepal district name"""
    if not ocr_text:
        return ocr_text
    
    import difflib
    
    # Clean the OCR text
    cleaned = ocr_text.strip().lower()
    cleaned_no_space = cleaned.replace(" ", "").replace("-", "")
    
    # Direct match (case-insensitive)
    for district in NEPAL_DISTRICTS:
        dist_lower = district.lower()
        if dist_lower == cleaned or dist_lower.replace(" ", "") == cleaned_no_space:
            return district
    
    # Fuzzy match using difflib
    matches = difflib.get_close_matches(cleaned_no_space, [d.lower() for d in NEPAL_DISTRICTS], n=1, cutoff=0.6 if len(cleaned_no_space) > 4 else 0.8)
    if matches:
        match_idx = [d.lower() for d in NEPAL_DISTRICTS].index(matches[0])
        return NEPAL_DISTRICTS[match_idx]
        
    return ocr_text


# ------------------ SECURITY HELPERS ------------------
def is_safe_filename(filename):
    """Check if filename is safe"""
    if not filename or filename == '':
        return False
    if '..' in filename:
        return False
    if filename.startswith('/') or filename.startswith('\\'):
        return False
    if '\0' in filename:
        return False
    return True

# ------------------ LOGGING SETUP ------------------
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/kyc_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ------------------ APP INIT ------------------
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    app.secret_key = 'dev-secret-key-change-me'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs('uploads', exist_ok=True)
os.makedirs('cache', exist_ok=True)

# Initialize database
create_table()

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'File too large. Max 16MB'}), 413

# ------------------ MODEL ------------------
model = None
nougat_processor = None
nougat_model = None
nougat_device = "cpu"

# Load model at startup
logger.info("Loading YOLO model...")
model_path = os.getenv('MODEL_PATH', r"C:\nagarikta\weights\best.pt")
try:
    if os.path.exists(model_path):
        model = YOLO(model_path)
        logger.info("Model loaded successfully")
    else:
        logger.error(f"Model not found at {model_path}")
        model = None
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    model = None

def get_nougat():
    global nougat_processor, nougat_model, nougat_device
    if nougat_processor is None or nougat_model is None:
        if NougatProcessor is None or VisionEncoderDecoderModel is None or torch is None:
            raise RuntimeError("Nougat dependencies are missing. Install torch and transformers.")
        nougat_device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Nougat model ({NOUGAT_MODEL_ID}) on {nougat_device}")
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
            logger.info(f"Nougat OCR failed, falling back to Tesseract: {e}")
    cfg = TESS_CONFIG_NEP if tess_lang == "nep" else TESS_CONFIG_ENG
    return pytesseract.image_to_string(crop_image, lang=tess_lang, config=cfg)

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
    logger.error(f"Swagger init error: {e}")

# ------------------ HELPERS ------------------
def allowed_file(*filenames):
    for fname in filenames:
        if '.' not in fname or fname.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
            return False
    return True

def preprocess_for_nepali(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Upscale heavily since Tesseract accuracy plummets below ~20-30px x-height
    scale = 2.5
    width = int(gray.shape[1] * scale)
    height = int(gray.shape[0] * scale)
    gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
    
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return Image.fromarray(thresh)


def deskew_image(pil_img):
    """Estimate skew angle and rotate image to deskew."""
    img = np.array(pil_img.convert("L"))
    _, th = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(th > 0))
    if coords.shape[0] < 10:
        return pil_img
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = img.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(np.array(pil_img), M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(rotated)


def preprocess_for_english(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Upscale heavily to enhance feature detection for Tesseract
    scale = 2.5
    width = int(gray.shape[1] * scale)
    height = int(gray.shape[0] * scale)
    gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
    
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    kernel = np.ones((1, 1), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return Image.fromarray(opened)


def preprocess_image(pil_img, tess_lang):
    """Language-aware preprocessing pipeline for OCR crops."""
    try:
        img = deskew_image(pil_img)
        if tess_lang == "nep":
            return preprocess_for_nepali(img)
        else:
            return preprocess_for_english(img)
    except Exception as e:
        logger.info(f"Preprocessing failed, using original crop: {e}")
        return pil_img

def normalize_ocr_text(text):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[©®™•·]", "", text)
    return text

def strip_generic_leading_label(text):
    match = re.match(
        r"^\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{1,40})\s*[:;._\-–—_\"'“”?]+\s*(.+)$",
        text,
    )
    if match:
        return match.group(2).strip()
    return text

def clean_perm_district(text):
    """Clean permanent district field"""
    text = normalize_ocr_text(text)
    # Remove prefix or suffix labels without deleting the actual value
    text = re.sub(r"(?i)\s*(?:permanent\s*)?(?:district|dist)\s*[:=.\-–—]*\s*", "", text).strip()
    text = re.sub(r"[^A-Za-z\s]", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_perm_address(text):
    """Clean permanent address field"""
    text = normalize_ocr_text(text)
    text = re.sub(r"(?i)^permanent\s*address\s*[:\-–—.]*\s*", "", text).strip()
    text = re.sub(r"(?i)^(?:metropolitan|metro)\s*[:\-–—.]*\s*", "", text).strip()
    text = re.sub(r"(?i)\s*[–—-]?\s*(?:district|dist)\s*[:=]*\s*.*$", "", text).strip()
    text = re.sub(r"[,._\-–—]+", " ", text).strip()
    text = re.sub(r"^[^\w]+|[^\w]+$", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text

def nepali_to_english_digits(text):
    """Convert Nepali digits to English digits and fix common OCR misreads"""
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

def nepali_to_roman(text):
    """Basic character mapping for fuzzy matching Nepali names to English"""
    if not text:
        return ""
    mapping = {
        'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
        'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
        'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
        'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
        'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
        'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh',
        'ष': 'sh', 'स': 's', 'ह': 'h', 'क्ष': 'ksh', 'त्र': 'tr', 'ज्ञ': 'gy',
        'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
        'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', 'ः': 'h',
        'अ': 'a', 'आ': 'a', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
        '्': ''
    }
    result = ""
    for char in text:
        result += mapping.get(char, char)
    return result.lower()

# Label variants commonly seen in OCR before actual values.
FIELD_PREFIX_PATTERNS = {
    0: [r"issued\s*office", r"office"],
    1: [
        r"name", r"full\s*name",
        r"नाम\s*थर",       # "name surname" label
        r"नाम\s*:",        # "name:" label with colon
        r"(?<![अ-ह])नाम(?!\s*(?:थर|द|देव|राज|बहादुर|कुमार|सिंह|प्रसाद))",  # bare "नाम" not part of a name
        r"जामषर",
        r"न[रत्राम]+\s*[थय][ररे]+", # Matches "नरम थरे", "नत्र थरे", etc.
        r"(?:नाम|नरम|नत्र|नताम)\s*(?:थर|थरे|थप|यरे)",
    ],
    2: [
        r"(?:father\s*'?s?)\s*name",
        r"(?:बुव(?:ाको|ुको)?|बाबु(?:को)?|हाबु(?:को)?|बुब)(?:को)?(?:\s*नर/?थेर)?",
        r"^.*थर[ः:]\s*",
        r"बुबुको\s*नर/?थेर",
        r"बाढ्को\s*हमिपर\s*रोपेत",
        r"बाढुकक्पोभिअर",
        r"बा[वुब]ुको\s*नाम\s*(?:थर|यर)?",
        r"बुवाको\s*नाम\s*(?:थर|यर)?",
        r"वुको\s*नाम\s*(?:थर|यर)?",
        r"वुको\s*नाम",
    ],
    3: [
        r"(?:mother\s*'?s?)\s*name",
        r"(?:आम(?:ाको|को)?|आमा)(?:\s*को)?(?:\s*नाम(?:\s*थर)?)?",
        r"^.*थर[ः:]\s*",
        r"आमाको\s*नाम(?:\s*थर)?",
        r"उक्किको\s*नाम\s*परः",
        r"जैँम्माको\s*नाम",
        r"लाको\s*नाम",
        r"धरः",
    ],
    4: [r"citizenship\s*(?:no|number)"],
    5: [r"full\s*name", r"name", r"^es\s+"],
    6: [r"sex", r"gender"],
    7: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*year", r"birth\s*year", r"year"],
    8: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*month", r"birth\s*month", r"month"],
    9: [r"(?:d\.?\s*o\.?\s*b|date\s*of\s*birth)\s*day", r"birth\s*day", r"day"],
    10: [r"permanent\s*district", r"district"],
    11: [r"permanent\s*address", r"address"],
    12: [r"ward\s*(?:no(?:w|\.)?|number)", r"(?:वर्ड|वर्ड)\s*(?:नं|नंबर|न०)"],
    13: [r"issued\s*date", r"date\s*of\s*issue", r"issue\s*date", r"जारीमिति", r"मिति"],
}

def strip_field_prefix(text, class_id):
    patterns = FIELD_PREFIX_PATTERNS.get(class_id, [])
    for base in patterns:
        text = re.sub(
            rf"(?i)\s*{base}\s*[:./\-–—_]*\s*",
            "",
            text,
            count=1
        )
    return text

# ========== NAME CORRECTION ENGINE ==========
def fix_nepali_name(text):
    """Fix common Tesseract OCR misreads in Nepali names."""
    if not text:
        return text

    # ---- Surname corrections: 
    text = re.sub(r'\bकन्द\b', 'चन्द', text)
    text = re.sub(r'\bकन्द्र\b', 'चन्द्र', text)
    text = re.sub(r'\bचंद\b', 'चन्द', text)
    text = re.sub(r'घन्द\b', 'चन्द', text)
    text = re.sub(r'\bचन्‍द\b', 'चन्द', text)   
    text = re.sub(r'\bचन्द्‌\b', 'चन्द्र', text)
    # Other common surname truncations / misreads
    text = re.sub(r'\bशाहा\b', 'शाह', text)
    text = re.sub(r'\bशाथ\b', 'शाह', text)
    text = re.sub(r'\bझार\b', 'झा', text)
    text = re.sub(r'\bपाण्ड\b', 'पाण्डे', text)
    text = re.sub(r'पाण्ड$', 'पाण्डे', text)
    text = re.sub(r'\bउप्रेत\b', 'उप्रेती', text)
    text = re.sub(r'उप्रेत$', 'उप्रेती', text)
    text = re.sub(r'\bतिवार\b', 'तिवारी', text)
    text = re.sub(r'तिवार$', 'तिवारी', text)
    text = re.sub(r'कार्क$', 'कार्की', text)
    text = re.sub(r'\bकार्क\b', 'कार्की', text)
    text = re.sub(r'बुढाथोक\b', 'बुढाथोकी', text)
    text = re.sub(r'\bठकर\b', 'ठकुरी', text)

    
    text = re.sub(r'^जु(सि|शि)', lambda m: 'शु' + m.group(1), text)
    text = re.sub(r'^जु(सी|शी)', lambda m: 'शु' + m.group(1), text)
    
    text = re.sub(r'(शुसि)त\b', r'\1ल', text)
    text = re.sub(r'(शुशि)त\b', r'\1ल', text)
   
    text = re.sub(r'^जमृता', 'अमृता', text)
    text = re.sub(r'^जमत', 'अमृत', text)
    text = re.sub(r'^जम्रित', 'अमृत', text)
    text = re.sub(r'^जनीता', 'अनीता', text)
    text = re.sub(r'^जनिता', 'अनिता', text)
    text = re.sub(r'^जनुराधा', 'अनुराधा', text)
    text = re.sub(r'^जञ्जली', 'अञ्जली', text)
    text = re.sub(r'^जम्बिका', 'अम्बिका', text)
    
    text = re.sub(r'(सुशी)त\b', r'\1ल', text)
    text = re.sub(r'(रोशा)त\b', r'\1ल', text)
    
    text = re.sub(r'^बिमला', 'विमला', text)
    text = re.sub(r'^बिष्णु', 'विष्णु', text)
    text = re.sub(r'^बिनोद', 'विनोद', text)
    text = re.sub(r'^बिकास', 'विकास', text)
    text = re.sub(r'^बिक्रम', 'विक्रम', text)

    text = re.sub(r'^वादुराम\b', 'बाबुराम', text)    
    text = re.sub(r'^वाबुराम\b', 'बाबुराम', text)    
    text = re.sub(r'^वाबु', 'बाबु', text)             
    text = re.sub(r'^वालु', 'बालु', text)           
    text = re.sub(r'^वालराम\b', 'बालराम', text)
    text = re.sub(r'^वाडा', 'बाडा', text)
    text = re.sub(r'^वसन्त', 'बसन्त', text)
    text = re.sub(r'^वसन्ता', 'बसन्ता', text)
    
    text = re.sub(r'\bवाबुराम\b', 'बाबुराम', text)   

    
    text = re.sub(r'बहदुर', 'बहादुर', text)
    text = re.sub(r'बाहदुर', 'बहादुर', text)
    text = re.sub(r'गहादुर', 'बहादुर', text)
    text = re.sub(r'बहादर', 'बहादुर', text)
    text = re.sub(r'दहादुर', 'बहादुर', text)
    text = re.sub(r'वहादुर', 'बहादुर', text)
    text = re.sub(r'भहादुर', 'बहादुर', text)
    text = re.sub(r'बहाँदुर', 'बहादुर', text)

    # ---- Compound name space insertion (missing spaces) ----
    # Insert space between common first-name and बहादुर when run together
    _bah_prefix = (
        r'(कर्ण|नर|टेक|कृष्ण|लाल|मन|राम|हरि|रण|धन|दिल|गण|हिम|विर|महा|रूप|सूर्य'
        r'|प्रेम|सूर|काल|खड्ग|इन्द्र|तुल|शक्ति|मोल|गोपाल|भक्त|ऐन|ब्रह)'
    )
    text = re.sub(_bah_prefix + r'(बहादुर)', r'\1 \2', text)
    # Insert space before कुमार / कुमारी when run together
    text = re.sub(r'([\u0900-\u097F]{2,})(कुमार|कुमारी)(?!\s)', r'\1 \2', text)
    # Insert space before known titles / suffixes run together
    text = re.sub(r'([\u0900-\u097F]{2,})(देवी|प्रसाद|राज|नाथ)(?!\s)', r'\1 \2', text)

    # ---- Spacing / punctuation artifacts ----
    text = re.sub(r'कुमारीसिंह', 'कुमारी सिंह', text)
    text = re.sub(r'कमारीसिंह', 'कुमारी सिंह', text)
    text = re.sub(r'कमारी', 'कुमारी', text)

    # Split common surnames from the first name when run together without space
    _surnames = r'(कार्की|खड्गी|भित्रकोटी|पुडासैनी|चन्द|शाह|थापा|श्रेष्ठ|मगर|गुरुङ|गुस्ङ|तामाङ|तामाङ्ग|गौचन|चौधरी|चौधर|लामा|लाम|बज्राचार्य|बब्राचार्य|स्याङतान|स्पाङतान|आचार्य|रेग्मी|रेग्म)'
    # Matches any non-space characters followed by the surname
    text = re.sub(r'([^\s]+)' + _surnames + r'\b', r'\1 \2', text)
    
    # Prefix garbage that slipped through
    text = re.sub(r'^धर\s+', '', text)
    text = re.sub(r'^रप\s+धर\s+', '', text)
    text = re.sub(r'^कबुको\s+', '', text)

    # ---- Singular character fixes ----
    text = re.sub(r'\bचौधर\b', 'चौधरी', text)
    text = re.sub(r'चौधर$', 'चौधरी', text)
    text = re.sub(r'\bलाम\b', 'लामा', text)
    text = re.sub(r'लाम$', 'लामा', text)
    text = re.sub(r'\bबब्राचार्य\b', 'बज्राचार्य', text)
    text = re.sub(r'बब्राचार्य$', 'बज्राचार्य', text)
    text = re.sub(r'\bस्पाङतान\b', 'स्याङतान', text)
    text = re.sub(r'स्पाङतान$', 'स्याङतान', text)
    text = re.sub(r'\bरेग्म\b', 'रेग्मी', text)
    text = re.sub(r'रेग्म$', 'रेग्मी', text)
    text = re.sub(r'\bगुस्ङ\b', 'गुरुङ', text)
    text = re.sub(r'गुस्ङ$', 'गुरुङ', text)
    text = re.sub(r'\bअमूृत', 'अमृत', text)
    text = re.sub(r'\bभन', 'धन', text)
    text = re.sub(r'^भन', 'धन', text)
    text = re.sub(r'\bअछाम\b', 'अछामी', text)
    text = re.sub(r'अछाम$', 'अछामी', text)
    text = re.sub(r'भमौम', 'भीम', text)
    text = re.sub(r'(?<!भ)भम(?!ौ)', 'भीम', text)
    text = re.sub(r'\bसिह\b', 'सिंह', text)
    text = re.sub(r'सिह$', 'सिंह', text)
    text = re.sub(r'सिह\s', 'सिंह ', text)
    text = re.sub(r'सपिर\b', 'समिर', text)
    text = re.sub(r'खइग\b', 'खड्गी', text)
    text = re.sub(r'खड्ग\b', 'खड्गी', text)
    text = re.sub(r'तिर्षमाया\b', 'तीर्थमाया', text)
    text = re.sub(r'निरौल\b', 'निरौला', text)
    text = re.sub(r'खतिवड\b', 'खतिवडा', text)
    text = re.sub(r'राजेद्र\b', 'राजेन्द्र', text)
    text = re.sub(r'भित्रकोट\b', 'भित्रकोटी', text)
    text = re.sub(r'भि्कोटौ\s*दमाई\b', 'भित्रकोटी दमाई', text)
    text = re.sub(r'शिबजी\s*कार्की\b', 'शिवजी कार्की', text)
    text = re.sub(r'जमुना\s*कार्की\b', 'जमुना कार्की', text)
    text = re.sub(r'भि्कोटौ\b', 'भित्रकोटी', text)
    text = re.sub(r'पुडासैन\b', 'पुडासैनी', text)
    text = re.sub(r'गोविदद्रैष्ठ\b', 'गोविन्द श्रेष्ठ', text)
    text = re.sub(r'मक्केश्रैष्ठ\b', 'मन्के श्रेष्ठ', text)
    text = re.sub(r'श्रैष्ठ\b', 'श्रेष्ठ', text)
    text = re.sub(r'मक्के\b', 'मन्के', text)
    text = re.sub(r'लिल्लाधर', 'लीलाधर', text)
    text = re.sub(r'बिश्ञात', 'बिशाल', text)
    text = re.sub(r'जर\s+बहादुर', 'नर बहादुर', text)
    text = re.sub(r'पु्णौ', 'पुर्णा', text)
    text = re.sub(r'थाप$', 'थापा', text)
    text = re.sub(r'थाप\s', 'थापा ', text)
    text = re.sub(r'थ्यप$', 'थापा', text)
    text = re.sub(r'थ्यप\s', 'थापा ', text)

    # ---- Noise / label fragments ----
    text = re.sub(r'प्रेम धरः जपरामकार्की', 'जयराम कार्की', text)
    text = re.sub(r'जपरामकार्की', 'जयराम कार्की', text)
    text = re.sub(r'धरः\s*', '', text)

    # ---- Double vowel cleanup ----
    text = re.sub(r'ीी', 'ी', text)
    text = re.sub(r'ाा', 'ा', text)
    text = re.sub(r'ेे', 'े', text)
    text = re.sub(r'ुु', 'ु', text)

    return text.strip()


# Mapping of romanised token → correct Nepali first-name
# (used by cross_correct_nepali_name to fix the front Nepali name
# when the back English name is more reliable)
_ENGLISH_TO_NEPALI_FIRST = {
    'shusil':   'शुसिल',
    'sushil':   'सुशील',
    'susheel':  'सुशील',
    'amrita':   'अमृता',
    'amrit':    'अमृत',
    'anita':    'अनिता',
    'anita':    'अनिता',
    'anuradha': 'अनुराधा',
    'anjali':   'अञ्जली',
    'ambika':   'अम्बिका',
    'vimala':   'विमला',
    'bimala':   'विमला',
    'vishnu':   'विष्णु',
    'binod':    'विनोद',
    'bikash':   'विकास',
    'bikram':   'विक्रम',
    'krishna':  'कृष्ण',
    'ram':      'राम',
    'hari':     'हरि',
    'laxmi':    'लक्ष्मी',
    'lakshmi':  'लक्ष्मी',
    'sita':     'सीता',
    'rita':     'रिता',
    'gita':     'गीता',
    'nirmala':  'निर्मला',
    'kamala':   'कमला',
    'sunita':   'सुनिता',
    'sarita':   'सरिता',
    'rekha':    'रेखा',
    'sabita':   'सविता',
    'savita':   'सविता',
    'kalpana':  'कल्पना',
    'mandira':  'मन्दिरा',
    'bibek':    'विवेक',
    'vivek':    'विवेक',
    'suresh':   'सुरेश',
    'mahesh':   'महेश',
    'ramesh':   'रमेश',
    'ganesh':   'गणेश',
    'dinesh':   'दिनेश',
    'rajesh':   'राजेश',
    'kamal':    'कमल',
    'naresh':   'नरेश',
    'prakash':  'प्रकाश',
    'anil':     'अनिल',
    'sunil':    'सुनिल',
    'kapil':    'कपिल',
    'rajan':    'राजन',
    'milan':    'मिलन',
    'narayan':  'नारायण',
    'gopal':    'गोपाल',
    'hari':     'हरि',
    'shiva':    'शिव',
    'dev':      'देव',
    'devi':     'देवी',
    'kumari':   'कुमारी',
    'bahadur':  'बहादुर',
    'chand':    'चन्द',
    'chandra':  'चन्द्र',
    'shah':     'शाह',
    'thapa':    'थापा',
    'karki':    'कार्की',
    'shrestha': 'श्रेष्ठ',
    'bhandari': 'भण्डारी',
    'paudel':   'पौडेल',
    'acharya':  'आचार्य',
    'adhikari': 'अधिकारी',
    'rai':      'राई',
    'tamang':   'तामाङ',
    'gurung':   'गुरुङ',
    'magar':    'मगर',
    'limbu':    'लिम्बू',
    'sherpa':   'शेर्पा',
    # newly added:
    'samir':      'समिर',
    'nitisha':    'नितिशा',
    'khadgi':     'खड्गी',
    'khadka':     'खड्का',
    'bhitrakoti': 'भित्रकोटी',
    'gauchan':    'गौचन',
    'samrakshan': 'संरक्षण',
    'pudasaini':  'पुडासैनी',
    'rama':       'रमा',
    'shibaji':    'शिबजी',
    'jamuna':     'जमुना',
    'navin':      'नविन',
    'nawin':      'नविन',
    'baburam':    'बाबुराम',
    'john':       'जोन',
    'jenifa':     'जेनिफा',
    'subam':      'शुवम',
    'shuvam':     'शुवम',
    'shubham':    'शुभम',
    
    # Common surnames
    'lama':       'लामा',
    'tamang':     'तामाङ',
    'chaudhary':  'चौधरी',
    'sherpa':     'शेर्पा',
    'magar':      'मगर',
    'bajracharya':'बज्राचार्य',
    'syangtan':   'स्याङतान',
    'acharya':    'आचार्य',
    'regmi':      'रेग्मी',
    'gurung':     'गुरुङ',
}


def cross_correct_nepali_name(nepali_name, english_name):
    """
    Use the back-side English name to detect and fix obvious first-name
    misreads in the front-side Nepali name.

    Strategy:
    - Split the English name into tokens
    - For each token, look up a canonical Nepali equivalent
    - If the Nepali name doesn't already contain that Nepali token
      (checked phonetically via nepali_to_roman), replace the first token
      in the Nepali name with the correct one.
    Returns the (possibly corrected) Nepali name.
    """
    if not nepali_name or not english_name:
        return nepali_name

    import difflib

    nep_tokens = nepali_name.split()
    eng_tokens = [t.lower() for t in english_name.split()]

    corrected_tokens = list(nep_tokens)  # copy

    for i, nep_tok in enumerate(nep_tokens):
        romanised = nepali_to_roman(nep_tok)
        # Find closest English token
        matches = difflib.get_close_matches(romanised, eng_tokens, n=1, cutoff=0.55)
        if not matches:
            continue
        eng_match = matches[0]
        # If there's a known canonical Nepali for that English token
        if eng_match in _ENGLISH_TO_NEPALI_FIRST:
            canonical = _ENGLISH_TO_NEPALI_FIRST[eng_match]
            # Only replace if the current token is "close enough" but not exact
            if nep_tok != canonical:
                logger.info(
                    f"cross_correct: '{nep_tok}' (romn='{romanised}') → '{canonical}' "
                    f"(via eng='{eng_match}')"
                )
                corrected_tokens[i] = canonical

    return ' '.join(corrected_tokens)
# =============================================
def clean_field_text(text, class_id):
    """Clean OCR text based on field type"""
    original = text
    text = normalize_ocr_text(text)

    if ":" in text or ";" in text:
        text = re.split(r"[:;]", text)[-1].strip()
    
    # address/district fields have their own helpers
    if class_id == 10:
        cleaned = clean_perm_district(text)
        if not cleaned and text.strip():
            cleaned = re.sub(r"(?i)^(?:permanent\s*)?(?:address[:\-–—._]*)?(?:metropolitan[:\-–—._]*)?(?:district|dist)\s*[:\-–—.]*\s*", "", text).strip()
            cleaned = re.sub(r"[^A-Za-z\s]", "", cleaned).strip()
        return cleaned
    if class_id == 11:
        cleaned = clean_perm_address(text)
        if not cleaned and text.strip():
            cleaned = re.sub(r"(?i)^permanent\s*address\s*[:\-–—.]*\s*", "", text).strip()
            cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", cleaned, flags=re.UNICODE).strip()
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    # Handle date component fields (year, month, day)
    if class_id in [7, 8, 9, 12]:  # year, month, day, ward_no
        text = strip_field_prefix(text, class_id)
        text = nepali_to_english_digits(text)
        
        if class_id == 8:  # Month field
            month_num = month_to_number(text)
            if month_num:
                return month_num
            numbers = re.findall(r"\d+", text)
            if numbers:
                month_val = int(numbers[0])
                if 1 <= month_val <= 12:
                    return str(month_val).zfill(2)
            return ""
        
        if class_id == 12:  # Ward number
            digits_only = re.sub(r"[^\d]", "", text).strip()
            if digits_only:
                try:
                    ward_val = int(digits_only)
                    if 1 <= ward_val <= 999:
                        return str(ward_val)
                except:
                    pass
            return ""
        
        text = re.sub(r"[^\d]", "", text).strip()
        return text

    # Handle issued date field
    if class_id == 13:
        t = normalize_ocr_text(text)
        t = strip_field_prefix(t, class_id)
        return t

    # Clean document/citizenship-like numbers
    if class_id == 4:
        t = nepali_to_english_digits(text)
        t = re.sub(r"[^0-9\-]", "", t)
        t = re.sub(r"-+", "-", t).strip("-")
        return t

        # Standard text field cleaning
    text = strip_field_prefix(text, class_id)
    text = strip_generic_leading_label(text)
    
    # ===== REMOVE "धर " FROM FATHER'S NAME =====
    if class_id == 2:
        text = re.sub(r'^धर\s*', '', text)
        text = re.sub(r'ब्वागुको\s*नाम\s*धरः\s*', '', text)
        text = re.sub(r'बाबुको\s*नाम\s*धरः\s*', '', text)
        text = re.sub(r'पिताको\s*नाम\s*', '', text)
        text = re.sub(r'^थब\s*', '', text)
        text = re.sub(r'\s+थब\s+', ' ', text)
    # ===========================================
    
    text = re.sub(r"^\W+|\W+$", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"\s+", " ", text).strip()

    # Apply name specific fixes
    if class_id in {1, 2, 3}:  # nepali names
        text = fix_nepali_name(text)

    # for name-like fields remove standalone garbage tokens
    if class_id in {1, 2, 3, 5}:
        tokens = text.split()
        kept = []
        stop_words = {"name", "full", "father", "mother", "gender", "sex", "dob", "date",
                      "neme", "nemes", "fuh", "ful", "fulll", 
                      "namae", "nams", "nam", "nem", "it",     
                      "of", "oy", "ofs", "oys", "s", "नामथर", "वुको नाम धरः", "नाम", "थब "}          
        for tok in tokens:
            low = tok.lower()
            if low in stop_words:
                continue
            if re.fullmatch(r"[A-Za-z\u0900-\u097F'’\-]+", tok):
                if re.search(r"[A-Z][a-z].*[A-Z]", tok):
                    continue
                if len(tok) == 1 and not re.match(r"[\u0900-\u097F]", tok) and len(tokens) > 1:
                    continue

                if re.search(r"[\u0900-\u097F]", tok):
                    nepali_vowel_marks = "ािीुूृेैोौं:ः"
                    vowel_count = sum(1 for ch in tok if ch in nepali_vowel_marks)
                    total_chars = len(tok)
                    if total_chars > 8 and vowel_count < (total_chars / 6):
                        continue

                kept.append(tok)
        text = " ".join(kept)
        if placeholder.get(class_id, "eng") == "nep" and not re.search(r"[\u0900-\u097F]", text):
            return ""

    for _ in range(2):
        if ":" in text or ";" in text:
            text = re.split(r"[:;]", text)[-1].strip()
            text = re.sub(r"^\W+|\W+$", "", text, flags=re.UNICODE).strip()
            if class_id in {1, 2, 3, 5}:
                text = strip_field_prefix(text, class_id)
                text = strip_generic_leading_label(text)

    if class_id == 3:
        text = re.sub(r'उअकैको\s*नाम\s*', '', text)
        text = re.sub(r'आमाको\s*नाम\s*', '', text)
        text = re.sub(r'माताको\s*नाम\s*', '', text)
        text = re.sub(r"धरः\s*", "", text).strip()
        text = re.sub(r"नाम\s*धरः\s*", "", text).strip()
        
        if re.fullmatch(r"[xX\.\s]{2,}", text):
            return ""
        if text.upper() in ("NA", "N/A", "NONE", "-", "--"):
            return ""
        if re.search(r"\d", text):
            return ""
        if text and not re.search(r"[aeiouAEIOU\u093E-\u094C]", text):
            return ""
        if len(text) < 3:
            return ""
        if re.fullmatch(r"[A-Za-z]+", text) and len(text) <= 4:
            if re.search(r"[bcdfghjklmnpqrstvwxyz]{3,}", text, re.IGNORECASE):
                return ""

    return text

def month_to_number(month_text):
    """Convert month name or Nepali month to month number (01-12)"""
    if not month_text:
        return ""
    
    month_text = normalize_ocr_text(str(month_text)).upper().strip()
    
    months = {
        "JAN": "01", "JANUARY": "01",
        "FEB": "02", "FEBRUARY": "02",
        "MAR": "03", "MARCH": "03",
        "APR": "04", "APRIL": "04",
        "MAY": "05",
        "JUN": "06", "JUNE": "06",
        "JUL": "07", "JULY": "07",
        "AUG": "08", "AUGUST": "08",
        "SEP": "09", "SEPTEMBER": "09",
        "OCT": "10", "OCTOBER": "10",
        "NOV": "11", "NOVEMBER": "11",
        "DEC": "12", "DECEMBER": "12",
    }
    
    if month_text in months:
        return months[month_text]
    
    for key, value in months.items():
        if month_text.startswith(key[:3]):
            return value
    
    match = re.search(r"(\d{1,2})", month_text)
    if match:
        month_num = int(match.group(1))
        if 1 <= month_num <= 12:
            return str(month_num).zfill(2)
    
    return ""

def parse_to_html_date(date_text):
    """Parse issued date in various formats (English and Nepali)"""
    if not date_text:
        return ""
    
    date_text = normalize_ocr_text(date_text)
    if not date_text:
        return ""
    
    date_text = nepali_to_english_digits(date_text)
    date_text = normalize_ocr_text(date_text)

    date_text = re.sub(r"(?i)(?:जारी\s*)?मिति\s*[:=]*\s*", "", date_text).strip()
    date_text = re.sub(r"(?i)(?:issued|date|dob|jari)\s*[:=]*\s*", "", date_text).strip()

    unified = re.sub(r"[^0-9]", "-", date_text)
    unified = re.sub(r"-+", "-", unified).strip("-")

    def try_fmt(y, m, d):
        try:
            yi = int(y); mi = int(m); di = int(d)
            if 1 <= mi <= 12 and 1 <= di <= 31 and 1900 <= yi <= 2200:
                return f"{y}-{str(mi).zfill(2)}-{str(di).zfill(2)}"
        except:
            pass
        return None

    mcombo = re.search(r"(\d{5,6})-(\d{1,2})-(\d{1,2})", unified)
    if mcombo:
        prefix, part2, part3 = mcombo.groups()
        year = prefix[:4]
        extra = prefix[4:]
        cand = try_fmt(year, extra, part3)
        if cand:
            return cand
        cand = try_fmt(year, extra + part2, part3)
        if cand:
            return cand
        cand = try_fmt(year, part2, part3)
        if cand:
            return cand

    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", unified)
    if match:
        res = try_fmt(*match.groups())
        if res:
            return res

    match = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", unified)
    if match:
        res = try_fmt(match.group(3), match.group(2), match.group(1))
        if res:
            return res

    m2 = re.search(r"(\d{8,10})", re.sub(r"-", "", unified))
    if m2:
        digits = m2.group(1)
        if len(digits) >= 8:
            y = digits[0:4]
            mo = digits[4:6]
            da = digits[6:8]
            res = try_fmt(y, mo, da)
            if res:
                return res

    all_digits = re.sub(r"\D", "", date_text)
    if all_digits:
        for L in (8, 7, 6):
            if len(all_digits) < L:
                continue
            for i in range(0, len(all_digits) - L + 1):
                sub = all_digits[i:i+L]
                if L >= 8:
                    y, mo, da = sub[0:4], sub[4:6], sub[6:8]
                    res = try_fmt(y, mo, da)
                    if res:
                        return res
                elif L == 7:
                    y = sub[0:4]
                    a, b = sub[4], sub[5:7]
                    res = try_fmt(y, a, b)
                    if res:
                        return res
                    a, b = sub[4:6], sub[6]
                    res = try_fmt(y, a, b)
                    if res:
                        return res
                elif L == 6:
                    y = sub[0:4]
                    a, b = sub[4], sub[5]
                    res = try_fmt(y, a, b)
                    if res:
                        return res

    return ""


def extract_nagrikta_number(fields, min_len=4):
    """Extract the first plausible Nagrikta/citizenship number"""
    if not fields:
        return ""
    for fld in fields:
        txt = fld.get('text') if isinstance(fld, dict) else str(fld)
        if not txt:
            continue
        txt = nepali_to_english_digits(str(txt))
        for m in re.finditer(r"(\d{1,})", txt):
            s = m.group(1)
            if len(s) >= min_len:
                return s.lstrip('0') or s
    return ""

# ========== POST-PROCESSING ==========
def post_process_extracted_data(data):
    # Gather the back-side English name once for cross-correction
    english_name_back = ""
    for item in data.get('back', []):
        if item['class_id'] == 5 and item.get('text'):
            # Strip OCR prefix noise from English name
            english_name_back = re.sub(r'(?i)^es\s+', '', item['text']).strip()
            break

    # Process front data
    for item in data.get('front', []):
        if item['class_id'] == 0 and item['text']:  # issued office
            if 'रलितपुर' in item['text']:
                item['text'] = item['text'].replace('रलितपुर', 'ललितपुर')

        elif item['class_id'] == 1 and item['text']:  # person's own Nepali name
            item['text'] = fix_nepali_name(item['text'])
            # Cross-correct using the back English name
            if english_name_back:
                item['text'] = cross_correct_nepali_name(item['text'], english_name_back)

        elif item['class_id'] == 2 and item['text']:  # father_name
            item['text'] = re.sub(r'^धर\s*', '', item['text'])
            item['text'] = re.sub(r'ब्वागुको\s*नाम\s*धरः\s*', '', item['text'])
            item['text'] = re.sub(r'बाबुको\s*नाम\s*धरः\s*', '', item['text'])
            item['text'] = re.sub(r'वुको\s*नाम\s*', '', item['text'])
            item['text'] = re.sub(r'पिताको\s*नाम\s*', '', item['text'])
            item['text'] = re.sub(r'धरः\s*', '', item['text'])
            item['text'] = re.sub(r'थब\s*', '', item['text'])
            item['text'] = fix_nepali_name(item['text'])

        elif item['class_id'] == 3 and item['text']:  # mother_name
            item['text'] = re.sub(r'जैँम्माको\s*नाम\s*', '', item['text'])
            item['text'] = re.sub(r'आमाको\s*नाम\s*', '', item['text'])
            item['text'] = re.sub(r'माताको\s*नाम\s*', '', item['text'])
            item['text'] = fix_nepali_name(item['text'])

    # Process back data
    for item in data.get('back', []):
        if item['class_id'] == 5 and item.get('text'):  # english name
            item['text'] = re.sub(r'(?i)^es\s+', '', item['text'])
            item['text'] = re.sub(r'(?i)^ree\s+', '', item['text'])
            item['text'] = re.sub(r'(?i)^ee\s+', '', item['text'])
            # Address garbage prefix ING commonly read from the top-left logo or watermark
            item['text'] = re.sub(r'(?i)^ing\w*\s*', '', item['text'])
            
            # Specific user-reported misreads
            item['text'] = re.sub(r'\bAASISA\b', 'AASISH', item['text'], flags=re.IGNORECASE)
            
            # Remove standalone "ING" misreads 
            item['text'] = re.sub(r'(?i)\bING\b', '', item['text'])
            
            # Normalize spacing / casing
            item['text'] = ' '.join(item['text'].upper().split())
        elif item['class_id'] == 6 and item['text']:  # gender
            g = item['text']
            g = re.sub(r'^Sex\s*', '', g)
            g = re.sub(r'(?i)femaic|femal[^e]', 'Female', g)
            g = re.sub(r'(?i)^mal[^e]', 'Male', g)
            # Normalise capitalisation
            if g.lower() in ('male', 'male.', 'male -'):
                g = 'Male'
            elif g.lower() in ('female', 'female.', 'female -'):
                g = 'Female'
            item['text'] = g.strip()
        elif item['class_id'] == 13:  # issue date
            item['text'] = re.sub(r'(?i)जारी[मभस]िति\s*[-—–]*\s*', '', item['text'])
            item['text'] = re.sub(r'(?i)जारी\s*[-—–]*\s*', '', item['text'])
            item['text'] = re.sub(r'(?i)मिति\s*[-—–]*\s*', '', item['text'])
            item['text'] = re.sub(r'\s+', '', item['text'])
        elif item['class_id'] == 4 and item['text']:  # citizenship number
            t = item['text']
            # Remove chars that are clearly not part of the number
            t = re.sub(r'[^0-9\-]', '', t).strip('-')
            if '-' not in t and len(t) >= 8:
                # Try to format as XX-XX-XX-XXXXX
                item['text'] = f"{t[:2]}-{t[2:4]}-{t[4:6]}-{t[6:]}"
            else:
                item['text'] = t
        elif item['class_id'] == 10 and item['text']:  # permanent district
            item['text'] = correct_district_name(item['text'])
        elif item['class_id'] == 11 and item['text']:  # permanent municipality
            item['text'] = correct_municipality_name(item['text'])

    return data
# =====================================

# ========== LLM REFINEMENT ==========
def gemini_refine_kyc(data, front_path, back_path):
    """Pass the post-processed OCR JSON along with the actual images to Gemini 1.5 for visual validation."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.warning("GEMINI_API_KEY not found. Skipping final LLM refinement.")
        return data
        
    try:
        import google.generativeai as genai
        import json
        from PIL import Image
        genai.configure(api_key=gemini_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Optimize image size to dramatically speed up API upload speed
        img_front = Image.open(front_path)
        img_front.thumbnail((1024, 1024))
        
        img_back = Image.open(back_path)
        img_back.thumbnail((1024, 1024))
        
        prompt = f"""
        You are an expert Nepali KYC Document data extractor and corrector. I have attached the original front and back images of a Nepali Citizenship Card.
        I have also provided a preliminary JSON data mapping extracted via a native OCR framework.
        
        CRITICAL SCHEMA MAPPING:
        The JSON contains `class_id` integers which perfectly map to explicit form fields. 
        Front Side Fields:
        - 0: Issue Office
        - 1: Person's Nepali Name
        - 2: Father's Name
        - 3: Mother's Name
        Back Side Fields:
        - 4: Citizenship Number
        - 5: Person's English Name
        - 6: Gender
        - 7: Date of Birth (Year)
        - 8: Date of Birth (Month)
        - 9: Date of Birth (Day)
        - 10: District
        - 11: Municipality
        - 12: Ward Number
        - 13: Full Issue Date (B.S.)

        Your task is to closely analyze the attached physical images, verify every single text entry strictly matching its corresponding `class_id` schema, and fix any OCR misspellings or typos natively reading from the picture.
        You MUST place the extracted strings precisely into their proper `class_id` objects.
        You must rely entirely on the provided images for truth. Extract the EXACT spellings as seen on the physical card.
        Return ONLY valid JSON sharing the EXACT same structure array as the input data. Do NOT use markdown code blocks (like ```json), just the naked raw JSON string.
        
        Initial OCR Data Array:
        {json.dumps(data, ensure_ascii=False)}
        """
        
        response = model.generate_content([prompt, img_front, img_back])
        text_resp = response.text.strip()
        
        # Clean up possible markdown code block wrappers
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.startswith("```"):
            text_resp = text_resp[3:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
            
        refined_data = json.loads(text_resp.strip())
        
        # Basic validation to ensure the LLM didn't break the structure
        if "front" in refined_data and "back" in refined_data:
            logger.info("Gemini LLM Refinement successful.")
            return refined_data
        else:
            logger.warning("Gemini LLM returned malformed structure. Falling back to original.")
            return data
            
    except Exception as e:
        logger.error(f"Gemini LLM Refinement failed: {e}")
        return data
# ====================================

# ------------------ ROUTES ------------------
@app.route("/", methods=['GET'])
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Serving index.html: {e}")
        return "Internal Server Error", 500

@app.route("/api/upload", methods=['POST'])
def upload_file():
    try:    
        if 'front' not in request.files or 'back' not in request.files:
            return jsonify({'error': 'Both files are required'}), 400

        front_file = request.files['front']
        back_file = request.files['back']

        if not front_file.filename or not back_file.filename:
            return jsonify({'error': 'Empty filename detected'}), 400
        if not is_safe_filename(front_file.filename) or not is_safe_filename(back_file.filename):
            return jsonify({'error': 'Invalid filename'}), 400
        if not allowed_file(front_file.filename, back_file.filename):
            return jsonify({'error': 'Invalid file extension'}), 400
        
        if model is None:
            logger.error("YOLO model not loaded")
            return jsonify({'error': 'OCR service unavailable'}), 503

        # Save uploaded files
        front_name = secure_filename(front_file.filename)
        back_name = secure_filename(back_file.filename)
        front_path = os.path.join(app.config['UPLOAD_FOLDER'], front_name)
        back_path = os.path.join(app.config['UPLOAD_FOLDER'], back_name)
        front_file.save(front_path)
        back_file.save(back_path)
        logger.info(f"Saved front image: {front_path}")
        logger.info(f"Saved back image: {back_path}")

        # Load images
        with Image.open(front_path) as front_pil:
            front_img = front_pil.convert("RGB")
        with Image.open(back_path) as back_pil:
            back_img = back_pil.convert("RGB")

        # YOLO prediction
        results = model.predict(source=[front_img, back_img], conf=0.5)
        logger.info("YOLO prediction completed")

        final_output = {"front": [], "back": []}

        # Validate Citizenship sides logic based on YOLO class predictions
        # Front classes: 0, 1, 2, 3
        # Back classes: 4, 5, 6, 7, 8, 9, 10, 11, 12, 13
        front_classes_expected = {0, 1, 2, 3}
        back_classes_expected = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13}

        # Results index 0 is front, index 1 is back
        front_boxes = getattr(results[0], 'boxes', None)
        back_boxes = getattr(results[1], 'boxes', None)

        front_detected_classes = set()
        back_detected_classes = set()

        if front_boxes is not None:
            for box in front_boxes.data.tolist():
                if len(box) > 5:
                    front_detected_classes.add(int(box[5]))

        if back_boxes is not None:
            for box in back_boxes.data.tolist():
                if len(box) > 5:
                    back_detected_classes.add(int(box[5]))

        # Count how many front-specific and back-specific classes are found in the uploaded "front"
        front_image_front_labels_count = len(front_detected_classes.intersection(front_classes_expected))
        front_image_back_labels_count = len(front_detected_classes.intersection(back_classes_expected))

        # Count how many front-specific and back-specific classes are found in the uploaded "back"
        back_image_back_labels_count = len(back_detected_classes.intersection(back_classes_expected))
        back_image_front_labels_count = len(back_detected_classes.intersection(front_classes_expected))

        logger.info(f"Validation step. Front image front/back labels: {front_image_front_labels_count}/{front_image_back_labels_count}")
        logger.info(f"Validation step. Back image front/back labels: {back_image_front_labels_count}/{back_image_back_labels_count}")

        # Basic "is it a document" check (require at least 2 relevant labels per side)
        total_front_labels = front_image_front_labels_count + front_image_back_labels_count
        total_back_labels = back_image_front_labels_count + back_image_back_labels_count
        
        if total_front_labels < 1 or total_back_labels < 2:
            return jsonify({'error': 'Invalid image: Please upload a clear picture of the citizenship card.'}), 400

        # Check for swapped sides
        # If the uploaded front has more back labels than front labels AND the uploaded back has more front labels than back labels
        if front_image_back_labels_count > front_image_front_labels_count and back_image_front_labels_count > back_image_back_labels_count:
            return jsonify({'error': 'Sides swapped: Please upload the Front side in the "front" field and the Back side in the "back" field.'}), 400
        
        # You could also add stricter front/back validation if needed
        if front_image_front_labels_count == 0:
            return jsonify({'error': 'Invalid front image: Could not detect front side features.'}), 400
        if back_image_back_labels_count < 2:
            return jsonify({'error': 'Invalid back image: Could not detect back side features.'}), 400

        for key, res, img in zip(["front", "back"], results, [front_img, back_img]):
            boxes = getattr(res, 'boxes', None)
            boxes_list = boxes.data.tolist() if boxes is not None else []
            for i, box in enumerate(boxes_list):
                try:
                    x1, y1, x2, y2 = map(int, box[:4])
                    conf = float(box[4]) if len(box) > 4 else 0.0
                    class_id = int(box[5]) if len(box) > 5 else 0
                except Exception as e:
                    logger.error(f"Box parsing error: {e}, box: {box}")
                    continue

                # Determine OCR language
                lang = placeholder.get(class_id, "eng")
                tess_lang = "nep" if lang == "nep" else "eng"

                # Crop and preprocess
                crop_img = img.crop((x1, y1, x2, y2))
                crop = preprocess_for_nepali(crop_img) if tess_lang == "nep" else crop_img

                # Save crop image
                crop_path = os.path.join(app.config['UPLOAD_FOLDER'], f"crop_{key}_{i}.png")
                try:
                    crop.save(crop_path)
                except Exception as e:
                    logger.error(f"Failed to save crop: {e}, path: {crop_path}")

                # OCR text
                text = ocr_text(crop, tess_lang)
                cleaned_text = clean_field_text(text, class_id)

                final_output[key].append({
                    "box_id": i,
                    "class_id": class_id,
                    "confidence": conf if np.isfinite(conf) else 0.0,
                    "text": cleaned_text
                })

        # Validate extracted nagarikta/citizenship numbers
        try:
            front_num = extract_nagrikta_number(final_output.get('front', []))
            back_num = extract_nagrikta_number(final_output.get('back', []))
            if front_num and back_num and front_num != back_num:
                return jsonify({'error': 'Nagrikta numbers do not match'}), 400
        except Exception as e:
            logger.warning(f"Nagrikta number check failed: {e}")

        # Cross-check Front (Nepali Name) and Back (English Name)
        try:
            front_name_text = ""
            for item in final_output.get('front', []):
                if item.get('class_id') == 1 and item.get('text'):
                    front_name_text = item.get('text')
                    break
                    
            back_name_text = ""
            for item in final_output.get('back', []):
                if item.get('class_id') == 5 and item.get('text'):
                    back_name_text = item.get('text')
                    break
            
            if front_name_text and back_name_text:
                import difflib
                romanized_front = nepali_to_roman(front_name_text)
                # Clean up punctuation and spaces for cleaner compare
                rf_clean = re.sub(r'[^a-z]', '', romanized_front.lower())
                bn_clean = re.sub(r'[^a-z]', '', back_name_text.lower())
                
                similarity = difflib.SequenceMatcher(None, rf_clean, bn_clean).ratio()
                logger.info(f"Name match similarity: {similarity:.2f} ({rf_clean} vs {bn_clean})")
                
                # If similarity is severely low, they are different people
                if similarity < 0.35 and len(rf_clean) > 3 and len(bn_clean) > 3:
                     return jsonify({'error': 'Mismatched ID: The front side and back side belong to different people.'}), 400
        except Exception as e:
            logger.warning(f"Name match validation failed: {e}")

        # Apply simple post-processing for father's name
        final_output = post_process_extracted_data(final_output)
        
        # Apply final multimodal LLM refinement if API key exists
        final_output = gemini_refine_kyc(final_output, front_path, back_path)

        session['kyc_data'] = final_output
        session['front_file'] = front_name
        session['back_file'] = back_name

        logger.info(f"Final OCR Output: {safe_json(final_output)}")
        
        # Save extracted data to cache
        try:
            cache_data = {
                'kyc_data': final_output,
                'front_file': front_name,
                'back_file': back_name
            }
            insert_kyc(cache_data)
            logger.info("KYC data saved to cache successfully")
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")

        kyc_url = url_for('kyc_form')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'redirect': kyc_url}), 200

        return redirect(kyc_url)

    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/kycform", methods=['GET'])
def kyc_form():
    kyc_data = session.get('kyc_data', {"front": [], "back": []})
    front_file = session.get('front_file', '')
    back_file = session.get('back_file', '')

    def get_text(data_list, class_id):
        for item in data_list:
            if item.get("class_id") == class_id and item.get("text"):
                return item["text"]
        return ""

        # Build prefill dictionary with all fields
    prefill = {
        # Basic Info
        "fullname": get_text(kyc_data.get("back", []), 5),
        "nepname": get_text(kyc_data.get("front", []), 1),
        "father_name": get_text(kyc_data.get("front", []), 2),
        "mother_name": get_text(kyc_data.get("front", []), 3),
        
        # Document Info
        "docnum": get_text(kyc_data.get("back", []), 4),
        "gender": get_text(kyc_data.get("back", []), 6),
        "issuedate": parse_to_html_date(get_text(kyc_data.get("back", []), 13)),
        
        # Permanent Address Info
        "perm_district": correct_district_name(get_text(kyc_data.get("back", []), 10)),
        # In your prefill dictionary, update the municipality line:
        "perm_municipality": correct_municipality_name(
            get_text(kyc_data.get("back", []), 11),
            get_text(kyc_data.get("back", []), 10)  # Pass district for context
        ),
        "perm_ward": get_text(kyc_data.get("back", []), 12),
        
        # Default values
        "nationality": "Nepali",
        "date": datetime.now().strftime("%Y-%m-%d"),
        
        # DOB fields
        "dob_year": get_text(kyc_data.get("back", []), 7),
        "dob_month": get_text(kyc_data.get("back", []), 8),
        "dob_day": get_text(kyc_data.get("back", []), 9),
    }
    
    if prefill["dob_year"] and prefill["dob_month"] and prefill["dob_day"]:
        try:
            dob_year = str(prefill["dob_year"]).strip()
            dob_month_raw = str(prefill["dob_month"]).strip().upper()
            dob_day = str(prefill["dob_day"]).strip()
            
            # Map text abbreviations to numeric strings
            month_map = {"JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06", 
                         "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"}
            for m_str, m_num in month_map.items():
                if m_str in dob_month_raw:
                    dob_month_raw = m_num
                    break
            
            dob_year = re.sub(r"\D", "", dob_year)
            dob_month = re.sub(r"\D", "", dob_month_raw).zfill(2)
            dob_day = re.sub(r"\D", "", dob_day).zfill(2)
            
            if len(dob_year) == 4 and len(dob_month) == 2 and len(dob_day) == 2:
                try:
                    month_int = int(dob_month)
                    day_int = int(dob_day)
                    if 1 <= month_int <= 12 and 1 <= day_int <= 31:
                        prefill["dob"] = f"{dob_year}-{dob_month}-{dob_day}"
                        logger.info(f"DOB constructed: {prefill['dob']}")
                except:
                    logger.info(f"DOB validation failed")
                    prefill["dob"] = ""
        except Exception as e:
            logger.error(f"DOB construction failed: {e}")
            prefill["dob"] = ""
    else:
        logger.info("Missing DOB components")

    return render_template(
        "kycform.html",
        front=front_file,
        back=back_file,
        prefill=prefill
    )

@app.route("/submit", methods=['POST'])
def submit_form():
    try:
        form_data = request.form.to_dict()
        
        photo = request.files.get('photo')
        signature = request.files.get('signature')
        
        if photo:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo.filename))
            photo.save(photo_path)
            form_data['photo_path'] = photo_path
            
        if signature:
            signature_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(signature.filename))
            signature.save(signature_path)
            form_data['signature_path'] = signature_path
        
        kyc_data = session.get('kyc_data', {})
        front_file = session.get('front_file', '')
        back_file = session.get('back_file', '')
        
        cache_data = {
            'kyc_data': kyc_data,
            'front_file': front_file,
            'back_file': back_file,
            'form_data': form_data
        }
        insert_kyc(cache_data)
        
        logger.info(f"Form submitted and saved to cache: {form_data}")
        
        return redirect(url_for('success'))
        
    except Exception as e:
        logger.error(f"Form submission error: {e}")
        return f"Error: {e}", 500

@app.route("/success")
def success():
    return """
    <html>
    <head>
        <title>Success - NIC Asia Bank</title>
        <style>
            body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; display: flex; justify-content: center; align-items: center; }
            .card { background: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
            h1 { color: #28a745; }
            a { display: inline-block; margin-top: 20px; padding: 10px 30px; background: #d32f2f; color: white; text-decoration: none; border-radius: 50px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>✓ KYC Application Submitted Successfully!</h1>
            <p>Thank you for submitting your KYC application.</p>
            <a href="/">Upload Another</a>
        </div>
    </body>
    </html>
    """

# ------------------ MAIN ------------------
if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        logger.error(f"App failed to start: {e}")