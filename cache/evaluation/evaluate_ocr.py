import os
import json
import numpy as np
import matplotlib.pyplot as plt
from jiwer import cer, wer
from sklearn.metrics import accuracy_score, classification_report

MODEL_OUTPUT_DIR = r"cache\evaluation\model_output"
GROUND_TRUTH_DIR = r"cache\evaluation\ground_truth"

all_gt = []
all_pred = []
confidences = []

cer_scores = []
wer_scores = []

def read_ground_truth(path):
    gt_dict = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            parts = line.strip().split(" ",1)
            idx = int(parts[0]) - 1
            text = parts[1]
            gt_dict[idx] = text

    return gt_dict


def extract_predictions(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    preds = {}

    for side in ["front","back"]:
        for item in data["extracted_data"][side]:

            cid = item["class_id"]
            text = item["text"]
            conf = item["confidence"]

            preds[cid] = text
            confidences.append(conf)

    return preds


for file in os.listdir(MODEL_OUTPUT_DIR):

    if not file.endswith(".json"):
        continue

    json_path = os.path.join(MODEL_OUTPUT_DIR,file)
    txt_path = os.path.join(GROUND_TRUTH_DIR,file.replace(".json",".txt"))

    if not os.path.exists(txt_path):
        print("Ground truth missing:",file)
        continue

    gt = read_ground_truth(txt_path)
    pred = extract_predictions(json_path)

    for key in gt:

        gt_text = gt[key]
        pred_text = pred.get(key,"")

        all_gt.append(gt_text)
        all_pred.append(pred_text)

        cer_scores.append(cer(gt_text,pred_text))
        wer_scores.append(wer(gt_text,pred_text))


# =========================
# Metrics
# =========================

exact_match = [1 if g==p else 0 for g,p in zip(all_gt,all_pred)]

accuracy = np.mean(exact_match)
avg_cer = np.mean(cer_scores)
avg_wer = np.mean(wer_scores)
avg_conf = np.mean(confidences)

print("\n===== OCR Evaluation Report =====\n")

print("Total Samples:",len(all_gt))
print("Exact Match Accuracy:",round(accuracy*100,2),"%")
print("Average CER:",round(avg_cer,4))
print("Average WER:",round(avg_wer,4))
print("Average Detection Confidence:",round(avg_conf,4))


# =========================
# Per Field Report
# =========================

print("\nClassification Style Report\n")

labels = list(set(all_gt))
print(classification_report(all_gt,all_pred,zero_division=0))


# =========================
# Visualization
# =========================

plt.figure()
plt.hist(cer_scores,bins=20)
plt.title("Character Error Rate Distribution")
plt.xlabel("CER")
plt.ylabel("Frequency")
plt.show()


plt.figure()
plt.hist(wer_scores,bins=20)
plt.title("Word Error Rate Distribution")
plt.xlabel("WER")
plt.ylabel("Frequency")
plt.show()


plt.figure()
plt.bar(["Accuracy","CER","WER"],
        [accuracy,avg_cer,avg_wer])

plt.title("OCR Performance Summary")
plt.show()


plt.figure()
plt.hist(confidences,bins=20)
plt.title("Detection Confidence Distribution")
plt.xlabel("Confidence")
plt.ylabel("Frequency")
plt.show()