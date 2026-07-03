import os
import json
import numpy as np
import matplotlib.pyplot as plt
from jiwer import cer, wer
from sklearn.metrics import classification_report

MODEL_OUTPUT_DIR = "cache/evaluation/model_output"
GROUND_TRUTH_DIR = "cache/evaluation/ground_truth"
RESULT_DIR = "evaluation_results"

# Create result folder
os.makedirs(RESULT_DIR, exist_ok=True)

all_gt = []
all_pred = []
confidences = []
field_classes = []  # Track class IDs for per-field analysis

cer_scores = []
wer_scores = []

# -----------------------------
# Read Ground Truth
# -----------------------------
def read_ground_truth(path):

    gt_dict = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f.readlines():

            line = line.strip()
            if not line:
                continue

            parts = line.split(" ", 1)
            if len(parts) < 2 or not parts[0].isdigit():
                # Skip malformed lines
                continue

            idx = int(parts[0]) - 1
            text = parts[1]

            gt_dict[idx] = text

    return gt_dict


# -----------------------------
# Extract Prediction
# -----------------------------
def extract_predictions(json_path):

    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Skipping invalid JSON ({os.path.basename(json_path)}): {e}")
            return None

    preds = {}

    for side in ["front","back"]:

        for item in data["extracted_data"][side]:

            cid = item["class_id"]
            text = item["text"]
            conf = item["confidence"]

            preds[cid] = text
            confidences.append(conf)

    return preds


# -----------------------------
# Process Files
# -----------------------------
for file in os.listdir(MODEL_OUTPUT_DIR):

    if not file.endswith(".json"):
        continue

    json_path = os.path.join(MODEL_OUTPUT_DIR,file)
    txt_path = os.path.join(GROUND_TRUTH_DIR,file.replace(".json",".txt"))

    if not os.path.exists(txt_path):
        print("Missing ground truth:",file)
        continue

    gt = read_ground_truth(txt_path)
    pred = extract_predictions(json_path)

    if pred is None:
        # Skip files where model output couldn't be parsed
        continue

    for key in gt:

        gt_text = gt[key]
        pred_text = pred.get(key,"")
        class_id = key  # Using key as class_id (assuming keys are class IDs)

        all_gt.append(gt_text)
        all_pred.append(pred_text)
        field_classes.append(class_id)

        cer_scores.append(cer(gt_text, pred_text))
        wer_scores.append(wer(gt_text, pred_text))


# -----------------------------
# Metrics
# -----------------------------

exact_match = [1 if g==p else 0 for g,p in zip(all_gt, all_pred)]

accuracy = np.mean(exact_match)
avg_cer = np.mean(cer_scores)
median_cer = np.median(cer_scores)
std_cer = np.std(cer_scores)
avg_wer = np.mean(wer_scores)
avg_conf = np.mean(confidences)

# -----------------------------
# Save Text Report
# -----------------------------

report_path = os.path.join(RESULT_DIR, "evaluation_report.txt")

with open(report_path, "w", encoding="utf-8") as f:

    f.write("=" * 50 + "\n")
    f.write("OCR EVALUATION REPORT\n")
    f.write("=" * 50 + "\n\n")

    f.write(f"Total Samples: {len(all_gt)}\n")
    f.write(f"Exact Match Accuracy: {accuracy*100:.2f}%\n")
    f.write(f"Average CER: {avg_cer:.4f}\n")
    f.write(f"Median CER: {median_cer:.4f}\n")
    f.write(f"Standard Deviation CER: {std_cer:.4f}\n")
    f.write(f"Average WER: {avg_wer:.4f}\n")
    f.write(f"Average Confidence: {avg_conf:.4f}\n\n")

    f.write("=" * 50 + "\n")
    f.write("Classification Report\n")
    f.write("=" * 50 + "\n\n")

    f.write(classification_report(all_gt, all_pred, zero_division=0))


# -----------------------------
# CER Histogram - IMPROVED VERSION
# -----------------------------

plt.figure(figsize=(10, 6))

# Create histogram
n, bins, patches = plt.hist(cer_scores, bins=20, color='steelblue', edgecolor='black', alpha=0.7)

# Add threshold line at acceptable error level (CER 0.5)
plt.axvline(x=0.5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Acceptable Error Threshold (CER 0.5)')

# Add mean line
plt.axvline(x=avg_cer, color='green', linestyle='-', linewidth=2, alpha=0.7, label=f'Mean CER: {avg_cer:.3f}')

# Add median line
plt.axvline(x=median_cer, color='orange', linestyle='-', linewidth=2, alpha=0.7, label=f'Median CER: {median_cer:.3f}')

# Labels and title
plt.title("Character Error Rate (CER) Distribution Across All Extracted Fields", fontsize=14, fontweight='bold')
plt.xlabel("Character Error Rate (CER)", fontsize=12)
plt.ylabel("Number of Fields", fontsize=12)

# Add grid for better readability
plt.grid(True, alpha=0.3, linestyle='--')

plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, "cer_distribution_improved.png"), dpi=300)
plt.close()


# -----------------------------
# WER Histogram - IMPROVED VERSION
# -----------------------------

plt.figure(figsize=(10, 6))

n, bins, patches = plt.hist(wer_scores, bins=20, color='coral', edgecolor='black', alpha=0.7)

plt.axvline(x=avg_wer, color='green', linestyle='-', linewidth=2, alpha=0.7, label=f'Mean WER: {avg_wer:.3f}')

plt.title("Word Error Rate (WER) Distribution Across All Extracted Fields", fontsize=14, fontweight='bold')
plt.xlabel("Word Error Rate (WER)", fontsize=12)
plt.ylabel("Number of Fields", fontsize=12)
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, "wer_distribution_improved.png"), dpi=300)
plt.close()


# -----------------------------
# Performance Summary - IMPROVED VERSION
# -----------------------------

plt.figure(figsize=(12, 5))

# Subplot 1: Accuracy
plt.subplot(1, 3, 1)
plt.bar(["Exact Match Accuracy"], [accuracy], color='green', edgecolor='black', width=0.5)
plt.ylim(0, 1)
plt.ylabel("Score")
plt.title(f"Accuracy: {accuracy*100:.1f}%")
plt.grid(True, alpha=0.3, axis='y')

# Subplot 2: Error Rates
plt.subplot(1, 3, 2)
bars = plt.bar(["CER", "WER"], [avg_cer, avg_wer], color=['orange', 'red'], edgecolor='black')
plt.ylabel("Error Rate")
plt.title(f"Average Error Rates")
plt.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{height:.3f}', ha='center', va='bottom', fontweight='bold')

# Subplot 3: Confidence
plt.subplot(1, 3, 3)
plt.bar(["Avg Confidence"], [avg_conf], color='purple', edgecolor='black', width=0.5)
plt.ylim(0, 1)
plt.ylabel("Score")
plt.title(f"Confidence: {avg_conf:.3f}")
plt.grid(True, alpha=0.3, axis='y')

plt.suptitle("OCR Performance Summary", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, "performance_summary_improved.png"), dpi=300)
plt.close()


# -----------------------------
# Confidence Distribution - IMPROVED VERSION
# -----------------------------

plt.figure(figsize=(10, 6))

n, bins, patches = plt.hist(confidences, bins=20, color='purple', edgecolor='black', alpha=0.7, range=(0, 1))

plt.axvline(x=avg_conf, color='red', linestyle='-', linewidth=2, alpha=0.7, label=f'Mean Confidence: {avg_conf:.3f}')
plt.axvline(x=0.5, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='Detection Threshold (0.5)')

plt.title("YOLOv8 Detection Confidence Distribution", fontsize=14, fontweight='bold')
plt.xlabel("Confidence Score", fontsize=12)
plt.ylabel("Number of Detections", fontsize=12)
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, "confidence_distribution_improved.png"), dpi=300)
plt.close()


# -----------------------------
# Per-Field Accuracy Bar Chart (if field_classes were tracked)
# -----------------------------
if field_classes:
    field_names = {
        1: "name_nep", 2: "father_name", 3: "mother_name",
        4: "citizenship_no", 5: "full_name_eng", 6: "sex",
        7: "dob_year", 8: "dob_month", 9: "dob_day",
        10: "perm_district", 11: "perm_address", 12: "perm_ward_no",
        13: "issued_date"
    }
    
    # Group by class_id
    field_accuracy = {}
    field_counts = {}
    
    for i, class_id in enumerate(field_classes):
        if class_id not in field_accuracy:
            field_accuracy[class_id] = []
            field_counts[class_id] = 0
        
        field_accuracy[class_id].append(exact_match[i])
        field_counts[class_id] += 1
    
    # Calculate average accuracy per field
    fields = []
    accuracies = []
    
    for class_id in sorted(field_accuracy.keys()):
        if class_id in field_names:
            fields.append(field_names[class_id])
            accuracies.append(np.mean(field_accuracy[class_id]) * 100)
    
    # Create horizontal bar chart
    plt.figure(figsize=(10, 8))
    colors = ['green' if acc > 90 else 'orange' if acc > 70 else 'red' for acc in accuracies]
    bars = plt.barh(fields, accuracies, color=colors, edgecolor='black')
    
    plt.xlabel("Accuracy (%)", fontsize=12)
    plt.title("OCR Accuracy by Field Type", fontsize=14, fontweight='bold')
    plt.xlim(0, 100)
    plt.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bar, acc) in enumerate(zip(bars, accuracies)):
        plt.text(acc + 1, bar.get_y() + bar.get_height()/2, f'{acc:.1f}%', 
                 va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULT_DIR, "field_accuracy.png"), dpi=300)
    plt.close()


# -----------------------------
# Completion Message
# -----------------------------

print("\n" + "=" * 50)
print("EVALUATION COMPLETED SUCCESSFULLY")
print("=" * 50)
print(f"Results saved in folder: {RESULT_DIR}")
print(f"\nFiles generated:")
print(f"  - evaluation_report.txt")
print(f"  - cer_distribution_improved.png")
print(f"  - wer_distribution_improved.png")
print(f"  - performance_summary_improved.png")
print(f"  - confidence_distribution_improved.png")
if field_classes:
    print(f"  - field_accuracy.png")
print("=" * 50)