# -*- coding: utf-8 -*-
"""
Phase 1: baseline classifier = TF-IDF (character n-grams) + Logistic Regression + calibration.

  Model A  trained on template train only        -> reproducible baseline numbers
  Model B  trained on template train + capped pool -> final model that the backend uses
            (pool cap = 40/category, chosen on the template test; tie with 60, smaller cap kept)

Threshold is chosen on complaints_test.csv (validation role, phrase-disjoint),
and final numbers are reported on complaints_external_test.csv (independent generator).
Run from the project root:  python ml/src/train_baseline.py
"""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA, MODELS, REPORTS = ROOT / "data", ROOT / "models", ROOT / "reports"
MODELS.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)

TARGET_ACC = 0.90        # accuracy we want on auto-routed complaints
POOL_CAP = 40           # max pool rows per category (pool is lopsided: mostly Hindi Water/Drainage)
MARGIN = 0.10            # top1 - top2 below this -> human review
SECONDARY_MIN = 0.25     # 2nd category above this -> attach as secondary note
LABELS = ["Roads", "Garbage", "Water Supply", "Drainage", "Streetlight", "Public Health", "Encroachment", "Other"]


def read(name):
    return pd.read_csv(DATA / name, encoding="utf-8-sig", keep_default_na=False)


def make_model():
    base = make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2),
        LogisticRegression(max_iter=2000, class_weight="balanced", C=5),
    )
    return CalibratedClassifierCV(base, method="sigmoid", cv=5)


def ece(conf, correct, bins=10):
    edges = np.linspace(0, 1, bins + 1); total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return total


def evaluate(name, model, df):
    pred = model.predict(df.text)
    out = {"macro_f1": f1_score(df.category, pred, average="macro")}
    for lang in ["English", "Hindi"]:
        m = (df.language == lang).values
        out[f"macro_f1_{lang}"] = f1_score(df.category[m], pred[m], average="macro")
    print(f"{name:<34} macro-F1 {out['macro_f1']:.3f} | English {out['macro_f1_English']:.3f} | Hindi {out['macro_f1_Hindi']:.3f}")
    return pred, out


train, pool = read("complaints_train.csv"), read("complaints_external_pool.csv")
val, ext = read("complaints_test.csv"), read("complaints_external_test.csv")

print("=== Model A: template train only ===")
A = make_model().fit(train.text, train.category)
_, a_val = evaluate("A on template test (unseen phrases)", A, val)
_, a_ext = evaluate("A on EXTERNAL test", A, ext)

print("\n=== Model B: template train + external pool (final) ===")
pool_capped = pd.concat([d.sample(min(len(d), POOL_CAP), random_state=1) for _, d in pool.groupby("category")])
print(f"pool rows used: {len(pool_capped)} of {len(pool)} (cap {POOL_CAP} per category)")
trainB = pd.concat([train, pool_capped], ignore_index=True)
B = make_model().fit(trainB.text, trainB.category)
_, b_val = evaluate("B on template test (unseen phrases)", B, val)
predB, b_ext = evaluate("B on EXTERNAL test", B, ext)
print("\nNOTE: B's pool and the external test come from the same generator (ChatGPT), so B's external score is a bit optimistic.")

print("\n--- classification report (B, external test) ---")
print(classification_report(ext.category, predB, labels=LABELS, digits=3))

# ---------------- confusion matrix
cm = confusion_matrix(ext.category, predB, labels=LABELS)
fig, ax = plt.subplots(figsize=(7, 6))
ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(8)); ax.set_xticklabels(LABELS, rotation=45, ha="right"); ax.set_yticks(range(8)); ax.set_yticklabels(LABELS)
for i in range(8):
    for j in range(8):
        ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=8)
ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title("Confusion matrix: model B on external test")
plt.tight_layout(); plt.savefig(REPORTS / "confusion_matrix_external.png", dpi=150); plt.close()

# ---------------- threshold from validation (template test), checked on external test
def curve(model, df):
    proba = model.predict_proba(df.text)
    top = proba.argmax(1); conf = proba.max(1)
    pred = model.classes_[top]; correct = (pred == df.category.values)
    srt = np.sort(proba, axis=1); gap = srt[:, -1] - srt[:, -2]
    rows = []
    for t in np.arange(0.40, 0.991, 0.01):
        keep = (conf >= t) & (gap >= MARGIN) & (pred != "Other")
        rows.append((round(float(t), 2), float(keep.mean()), float(correct[keep].mean()) if keep.any() else np.nan))
    return pd.DataFrame(rows, columns=["threshold", "coverage", "accuracy"]), conf, correct

cv_val, conf_val, ok_val = curve(B, val)
cv_ext, conf_ext, ok_ext = curve(B, ext)
good = cv_val[cv_val.accuracy >= TARGET_ACC]
threshold = float(good.threshold.iloc[0]) if len(good) else 0.90
print(f"\nChosen threshold (validation accuracy >= {TARGET_ACC:.0%} on auto-routed): {threshold}")
for name, c in [("validation (template test)", cv_val), ("EXTERNAL test", cv_ext)]:
    r = c[c.threshold == threshold].iloc[0]
    print(f"  {name:<28} auto-routed {r.coverage:.1%} at accuracy {r.accuracy:.1%}")

plt.figure(figsize=(7, 4.5))
plt.plot(cv_val.coverage, cv_val.accuracy, label="validation (template test)")
plt.plot(cv_ext.coverage, cv_ext.accuracy, label="external test")
plt.axvline(float(cv_val[cv_val.threshold == threshold].coverage.iloc[0]), ls=":", c="gray")
plt.xlabel("Coverage (share auto-routed)"); plt.ylabel("Accuracy on auto-routed"); plt.title("Coverage vs accuracy (model B)")
plt.legend(); plt.grid(alpha=.3); plt.tight_layout(); plt.savefig(REPORTS / "coverage_vs_accuracy.png", dpi=150); plt.close()

# ---------------- reliability diagram + ECE (external test)
bins = np.linspace(0.2, 1, 9); xs, ys = [], []
for lo, hi in zip(bins[:-1], bins[1:]):
    m = (conf_ext > lo) & (conf_ext <= hi)
    if m.sum() >= 5:
        xs.append(conf_ext[m].mean()); ys.append(ok_ext[m].mean())
ece_ext, ece_val = ece(conf_ext, ok_ext), ece(conf_val, ok_val)
plt.figure(figsize=(5, 5)); plt.plot([0, 1], [0, 1], "k--", label="perfect"); plt.plot(xs, ys, "o-", label=f"model B (ECE {ece_ext:.3f})")
plt.xlabel("Predicted confidence"); plt.ylabel("Actual accuracy"); plt.title("Reliability diagram (external test)")
plt.legend(); plt.grid(alpha=.3); plt.tight_layout(); plt.savefig(REPORTS / "reliability_diagram.png", dpi=150); plt.close()
print(f"ECE: validation {ece_val:.3f}, external {ece_ext:.3f}  (lower is better; 0 = honest confidence)")

# ---------------- save
joblib.dump(B, MODELS / "model.joblib")
joblib.dump(A, MODELS / "model_template_only.joblib")
cfg = {"threshold": threshold, "margin": MARGIN, "secondary_min": SECONDARY_MIN, "target_accuracy": TARGET_ACC,
       "classes": list(B.classes_)}
(MODELS / "routing_config.json").write_text(json.dumps(cfg, indent=2))
metrics = {"model_A_template_only": {"template_test": a_val, "external_test": a_ext},
           "model_B_template_plus_pool": {"template_test": b_val, "external_test": b_ext},
           "threshold": threshold, "ece_validation": ece_val, "ece_external": ece_ext,
           "coverage_accuracy_external_at_threshold": cv_ext[cv_ext.threshold == threshold].iloc[0].to_dict()}
(REPORTS / "metrics.json").write_text(json.dumps(metrics, indent=2))
cv_ext.to_csv(REPORTS / "coverage_curve_external.csv", index=False)
print("\nSaved: ml/models/model.joblib, routing_config.json, ml/reports/*.png, metrics.json")
