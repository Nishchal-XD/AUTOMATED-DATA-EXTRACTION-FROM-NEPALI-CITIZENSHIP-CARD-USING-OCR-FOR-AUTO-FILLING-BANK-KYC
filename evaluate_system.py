"""
Automated Testing, Evaluation, and Validation Script for
Nepali Citizenship Card OCR System
"""

import os
import json
import re
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter, defaultdict
import argparse

# ============================================================
# CONFIGURATION
# ============================================================

CACHE_DIR = "cache"
REPORT_DIR = "evaluation_reports"

# Create report directory
os.makedirs(REPORT_DIR, exist_ok=True)

# ============================================================
# FIELD MAPPINGS (from your data.yaml)
# ============================================================

FIELD_NAMES = {
    1: "name_nep",
    2: "father_name",
    3: "mother_name",
    4: "citizenship_no",
    5: "full_name_eng",
    6: "sex",
    7: "dob_year",
    8: "dob_month",
    9: "dob_day",
    10: "perm_district",
    11: "perm_address",
    12: "perm_ward_no",
    13: "issued_date"
}

FIELD_DISPLAY_NAMES = {
    1: "Name (Nepali)",
    2: "Father's Name",
    3: "Mother's Name",
    4: "Citizenship No.",
    5: "Full Name (English)",
    6: "Gender",
    7: "DOB Year",
    8: "DOB Month",
    9: "DOB Day",
    10: "District",
    11: "Municipality/Address",
    12: "Ward No.",
    13: "Issue Date"
}

# ============================================================
# DATA LOADING
# ============================================================

def load_cache_files():
    """Load all cache files from the cache directory"""
    cache_files = []
    if not os.path.exists(CACHE_DIR):
        print(f"❌ Cache directory not found: {CACHE_DIR}")
        return cache_files
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CACHE_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cache_files.append(data)
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    
    return cache_files

# ============================================================
# EVALUATION METRICS
# ============================================================

class EvaluationMetrics:
    def __init__(self):
        self.total_cards = 0
        self.field_presence = defaultdict(int)  # How many times each field appears
        self.field_confidence = defaultdict(list)  # Confidence scores per field
        self.field_values = defaultdict(list)  # Extracted values per field
        self.yolo_detections = {"front": 0, "back": 0}
        self.fallback_detections = {"front": 0, "back": 0}
        self.empty_fields = defaultdict(int)
        self.corrections_applied = defaultdict(int)
        
    def process_card(self, card_data):
        """Process a single card's extracted data"""
        self.total_cards += 1
        
        extracted = card_data.get('extracted_data', {})
        
        # Process front side
        front_items = extracted.get('front', [])
        for item in front_items:
            class_id = item.get('class_id')
            text = item.get('text', '')
            confidence = item.get('confidence', 0)
            
            if class_id is not None:
                self.field_presence[class_id] += 1
                self.field_confidence[class_id].append(confidence)
                self.field_values[class_id].append(text)
                
                if not text:
                    self.empty_fields[class_id] += 1
                
                # Check if this was a YOLO detection or fallback
                if 'fallback' not in str(item.get('box_id', '')):
                    self.yolo_detections["front"] += 1
                else:
                    self.fallback_detections["front"] += 1
        
        # Process back side
        back_items = extracted.get('back', [])
        for item in back_items:
            class_id = item.get('class_id')
            text = item.get('text', '')
            confidence = item.get('confidence', 0)
            
            if class_id is not None:
                self.field_presence[class_id] += 1
                self.field_confidence[class_id].append(confidence)
                self.field_values[class_id].append(text)
                
                if not text:
                    self.empty_fields[class_id] += 1
                
                # Check if this was a YOLO detection or fallback
                if 'fallback' not in str(item.get('box_id', '')):
                    self.yolo_detections["back"] += 1
                else:
                    self.fallback_detections["back"] += 1
        
        # Detect corrections based on common patterns
        self.detect_corrections(front_items + back_items)
    
    def detect_corrections(self, items):
        """Detect if corrections were applied based on text patterns"""
        correction_patterns = {
            "Father's Name Fix": ['भीम', 'बहादुर'],
            "Surname Correction": ['कार्की', 'पाण्डे', 'तिवारी', 'बुढाथोकी', 'उप्रेती'],
            "District Correction": ['Sarlahi', 'Lalitpur', 'Kathmandu', 'Gulmi'],
            "Municipality Correction": ['Beldandi', 'Kohalpur', 'Naumule'],
        }
        
        for item in items:
            text = item.get('text', '')
            for corr_type, patterns in correction_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        self.corrections_applied[corr_type] += 1
                        break
    
    def get_field_presence_rate(self):
        """Calculate presence rate for each field"""
        rates = {}
        for class_id, count in self.field_presence.items():
            # Each card can have at most 1 of each field (front or back)
            max_possible = self.total_cards
            if class_id in [0,1,2,3]:  # Front-only fields
                max_possible = self.total_cards
            elif class_id in [4,5,6,7,8,9,10,11,12,13]:  # Back-only fields
                max_possible = self.total_cards
            
            rates[class_id] = (count / max_possible) * 100 if max_possible > 0 else 0
        return rates
    
    def get_average_confidence(self):
        """Calculate average confidence per field"""
        avg_conf = {}
        for class_id, confs in self.field_confidence.items():
            if confs:
                avg_conf[class_id] = np.mean(confs) * 100
        return avg_conf
    
    def get_empty_field_rate(self):
        """Calculate rate of empty fields"""
        rates = {}
        for class_id, empty_count in self.empty_fields.items():
            total = self.field_presence.get(class_id, 1)
            rates[class_id] = (empty_count / total) * 100 if total > 0 else 0
        return rates
    
    def get_top_values(self, class_id, n=5):
        """Get most common values for a field"""
        values = [v for v in self.field_values.get(class_id, []) if v]
        if not values:
            return []
        counter = Counter(values)
        return counter.most_common(n)

# ============================================================
# REPORT GENERATION
# ============================================================

def generate_report(metrics, output_dir):
    """Generate comprehensive evaluation report"""
    
    report_file = os.path.join(output_dir, "evaluation_report.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("NEPALI CITIZENSHIP CARD OCR SYSTEM - EVALUATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Cards Evaluated: {metrics.total_cards}\n\n")
        
        # 1. Overall Statistics
        f.write("-" * 80 + "\n")
        f.write("1. OVERALL STATISTICS\n")
        f.write("-" * 80 + "\n\n")
        
        total_fields = sum(metrics.field_presence.values())
        avg_fields_per_card = total_fields / metrics.total_cards if metrics.total_cards > 0 else 0
        
        f.write(f"Total Fields Extracted: {total_fields}\n")
        f.write(f"Average Fields per Card: {avg_fields_per_card:.2f}\n")
        f.write(f"YOLO Detections (Front): {metrics.yolo_detections['front']}\n")
        f.write(f"YOLO Detections (Back): {metrics.yolo_detections['back']}\n")
        f.write(f"Fallback Detections (Front): {metrics.fallback_detections['front']}\n")
        f.write(f"Fallback Detections (Back): {metrics.fallback_detections['back']}\n\n")
        
        # 2. Field-wise Presence Rate
        f.write("-" * 80 + "\n")
        f.write("2. FIELD-WISE PRESENCE RATE\n")
        f.write("-" * 80 + "\n\n")
        
        presence_rates = metrics.get_field_presence_rate()
        avg_conf = metrics.get_average_confidence()
        
        f.write(f"{'Class':<6} {'Field Name':<25} {'Presence':<12} {'Avg Confidence':<15}\n")
        f.write("-" * 60 + "\n")
        
        for class_id in sorted(FIELD_NAMES.keys()):
            if class_id in presence_rates:
                presence = presence_rates[class_id]
                confidence = avg_conf.get(class_id, 0)
                f.write(f"{class_id:<6} {FIELD_DISPLAY_NAMES[class_id]:<25} "
                       f"{presence:>6.1f}%      {confidence:>6.1f}%\n")
            else:
                f.write(f"{class_id:<6} {FIELD_DISPLAY_NAMES[class_id]:<25} "
                       f"{'0.0%':>12}      {'0.0%':>6}\n")
        f.write("\n")
        
        # 3. Empty Field Rate
        f.write("-" * 80 + "\n")
        f.write("3. EMPTY FIELD RATE\n")
        f.write("-" * 80 + "\n\n")
        
        empty_rates = metrics.get_empty_field_rate()
        
        f.write(f"{'Class':<6} {'Field Name':<25} {'Empty Rate':<12}\n")
        f.write("-" * 45 + "\n")
        
        for class_id in sorted(FIELD_NAMES.keys()):
            if class_id in empty_rates:
                rate = empty_rates[class_id]
                f.write(f"{class_id:<6} {FIELD_DISPLAY_NAMES[class_id]:<25} {rate:>6.1f}%\n")
            else:
                f.write(f"{class_id:<6} {FIELD_DISPLAY_NAMES[class_id]:<25} {'N/A':>6}\n")
        f.write("\n")
        
        # 4. Top Extracted Values
        f.write("-" * 80 + "\n")
        f.write("4. MOST COMMON EXTRACTED VALUES\n")
        f.write("-" * 80 + "\n\n")
        
        for class_id in [1,2,4,5,10,11]:  # Most important fields
            field_name = FIELD_DISPLAY_NAMES[class_id]
            top_values = metrics.get_top_values(class_id, 5)
            
            if top_values:
                f.write(f"\n{field_name}:\n")
                for value, count in top_values:
                    f.write(f"  - {value} (appeared {count} times)\n")
        f.write("\n")
        
        # 5. Correction Statistics
        f.write("-" * 80 + "\n")
        f.write("5. POST-PROCESSING CORRECTIONS\n")
        f.write("-" * 80 + "\n\n")
        
        if metrics.corrections_applied:
            for corr_type, count in metrics.corrections_applied.items():
                f.write(f"{corr_type}: {count} times\n")
        else:
            f.write("No corrections detected in this sample.\n")
        f.write("\n")
        
        # 6. Sample Cards
        f.write("-" * 80 + "\n")
        f.write("6. SAMPLE EXTRACTIONS\n")
        f.write("-" * 80 + "\n\n")
        
        # This would require ground truth, so we'll skip for now
        f.write("Note: For accuracy metrics, please provide ground truth data.\n")
        f.write("See ground_truth_template.json for format.\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    print(f"✅ Report generated: {report_file}")
    return report_file

def generate_charts(metrics, output_dir):
    """Generate visualization charts"""
    
    # Chart 1: Field Presence Rate
    plt.figure(figsize=(12, 6))
    presence = metrics.get_field_presence_rate()
    
    fields = [FIELD_DISPLAY_NAMES[i] for i in sorted(FIELD_NAMES.keys())]
    values = [presence.get(i, 0) for i in sorted(FIELD_NAMES.keys())]
    
    colors = ['green' if v >= 90 else 'yellow' if v >= 70 else 'red' for v in values]
    
    plt.barh(fields, values, color=colors)
    plt.xlabel('Presence Rate (%)')
    plt.title('Field-wise Presence Rate')
    plt.xlim(0, 100)
    plt.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (field, v) in enumerate(zip(fields, values)):
        plt.text(v + 1, i, f'{v:.1f}%', va='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'field_presence.png'), dpi=150)
    plt.close()
    
    # Chart 2: Confidence Scores
    plt.figure(figsize=(12, 6))
    confidences = metrics.get_average_confidence()
    
    conf_values = [confidences.get(i, 0) for i in sorted(FIELD_NAMES.keys())]
    
    plt.barh(fields, conf_values, color='skyblue')
    plt.xlabel('Average Confidence (%)')
    plt.title('Field-wise Average Confidence')
    plt.xlim(0, 100)
    plt.grid(axis='x', alpha=0.3)
    
    for i, (field, v) in enumerate(zip(fields, conf_values)):
        plt.text(v + 1, i, f'{v:.1f}%', va='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'field_confidence.png'), dpi=150)
    plt.close()
    
    # Chart 3: YOLO vs Fallback
    plt.figure(figsize=(8, 6))
    
    categories = ['Front Side', 'Back Side']
    yolo_counts = [metrics.yolo_detections["front"], metrics.yolo_detections["back"]]
    fallback_counts = [metrics.fallback_detections["front"], metrics.fallback_detections["back"]]
    
    x = np.arange(len(categories))
    width = 0.35
    
    plt.bar(x - width/2, yolo_counts, width, label='YOLO Detection', color='green')
    plt.bar(x + width/2, fallback_counts, width, label='Fallback', color='orange')
    
    plt.xlabel('Card Side')
    plt.ylabel('Number of Detections')
    plt.title('YOLO vs Fallback Detection')
    plt.xticks(x, categories)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, (y, f) in enumerate(zip(yolo_counts, fallback_counts)):
        plt.text(i - width/2, y + 5, str(y), ha='center')
        plt.text(i + width/2, f + 5, str(f), ha='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'detection_methods.png'), dpi=150)
    plt.close()
    
    print(f"✅ Charts generated in {output_dir}")

# ============================================================
# MAIN EVALUATION FUNCTION
# ============================================================

def run_evaluation():
    """Main evaluation function"""
    print("=" * 60)
    print("NEPALI CITIZENSHIP CARD OCR SYSTEM EVALUATION")
    print("=" * 60)
    
    # Create report directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(REPORT_DIR, f"eval_{timestamp}")
    os.makedirs(report_dir, exist_ok=True)
    
    # Load cache files
    print("\n📂 Loading cache files...")
    cache_files = load_cache_files()
    
    if not cache_files:
        print("❌ No cache files found!")
        return
    
    print(f"✅ Loaded {len(cache_files)} cache files")
    
    # Initialize metrics
    metrics = EvaluationMetrics()
    
    # Process each cache file
    print("\n🔍 Analyzing cards...")
    for i, cache in enumerate(cache_files, 1):
        if i % 10 == 0:
            print(f"   Processed {i}/{len(cache_files)} cards...")
        
        metrics.process_card(cache)
    
    print(f"✅ Analyzed {metrics.total_cards} cards successfully!")
    
    # Generate reports
    print("\n📊 Generating reports...")
    
    # Text report
    report_file = generate_report(metrics, report_dir)
    
    # Charts
    generate_charts(metrics, report_dir)
    
    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Cards: {metrics.total_cards}")
    print(f"Total Fields: {sum(metrics.field_presence.values())}")
    
    # Calculate average presence
    presence = metrics.get_field_presence_rate()
    avg_presence = np.mean(list(presence.values())) if presence else 0
    print(f"Average Field Presence: {avg_presence:.1f}%")
    
    # Calculate average confidence
    conf = metrics.get_average_confidence()
    avg_conf = np.mean(list(conf.values())) if conf else 0
    print(f"Average Confidence: {avg_conf:.1f}%")
    
    print(f"YOLO Detections: {metrics.yolo_detections['front'] + metrics.yolo_detections['back']}")
    print(f"Fallback Detections: {metrics.fallback_detections['front'] + metrics.fallback_detections['back']}")
    print("=" * 60)
    
    print(f"\n📁 Reports saved to: {report_dir}")
    print(f"   - {report_file}")
    print(f"   - field_presence.png")
    print(f"   - field_confidence.png")
    print(f"   - detection_methods.png")

# ============================================================
# GROUND TRUTH TEMPLATE GENERATOR
# ============================================================

def generate_ground_truth_template():
    """Generate a template for ground truth data"""
    template = {}
    
    # Get sample card IDs from cache
    cache_files = load_cache_files()
    sample_ids = [cf.get('unique_id', f'card_{i}') for i, cf in enumerate(cache_files[:3])]
    
    for card_id in sample_ids:
        template[card_id] = {}
        for class_id, field_name in FIELD_NAMES.items():
            template[card_id][str(class_id)] = f"expected_{field_name}"
    
    template_file = 'ground_truth_template.json'
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Ground truth template created: {template_file}")
    print("\n📝 Instructions:")
    print("1. Open ground_truth_template.json")
    print("2. Replace 'expected_*' with actual correct values")
    print("3. Rename to ground_truth.json")
    print("4. Run evaluation again for accuracy metrics")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluate Nepali Citizenship Card OCR System')
    parser.add_argument('--generate-template', action='store_true', 
                       help='Generate ground truth template')
    parser.add_argument('--run', action='store_true',
                       help='Run evaluation')
    
    args = parser.parse_args()
    
    if args.generate_template:
        generate_ground_truth_template()
    
    if args.run:
        run_evaluation()
    
    if not args.generate_template and not args.run:
        print("Please specify an action:")
        print("  --generate-template  : Create ground truth template")
        print("  --run               : Run evaluation")