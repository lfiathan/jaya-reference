"""Shared, explicit schema for training and serving."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEM = "Curricular_units_1st_sem_"
FEATURES = ["Course", "Daytime_evening_attendance", "Previous_qualification_grade", "Admission_grade"] + [SEM + s for s in ["credited", "enrolled", "evaluations", "approved", "grade", "without_evaluations"]]
CATEGORICAL = ["Course", "Daytime_evening_attendance"]
NUMERIC = [c for c in FEATURES if c not in CATEGORICAL]
COURSES = {33:"Biofuel Production Technologies",171:"Animation and Multimedia Design",8014:"Social Service (evening)",9003:"Agronomy",9070:"Communication Design",9085:"Veterinary Nursing",9119:"Informatics Engineering",9130:"Equinculture",9147:"Management",9238:"Social Service",9254:"Tourism",9500:"Nursing",9556:"Oral Hygiene",9670:"Advertising and Marketing Management",9773:"Journalism and Communication",9853:"Basic Education",9991:"Management (evening)"}

def load_data():
    return pd.read_csv(ROOT / "data/students_performance.csv", sep=";", encoding="utf-8-sig")

def validate_inputs(frame):
    missing = sorted(set(FEATURES) - set(frame.columns))
    if missing:
        raise ValueError("Kolom belum tersedia: " + ", ".join(missing))
    x = frame[FEATURES].copy()
    try:
        x = x.apply(pd.to_numeric, errors="raise")
    except (TypeError, ValueError):
        raise ValueError("Semua input model harus berupa angka/kode numerik.") from None
    if x.empty or not np.isfinite(x.to_numpy()).all():
        raise ValueError("Input harus berisi baris, tanpa nilai kosong atau tak hingga.")
    if not x.Course.isin(COURSES).all() or not x.Daytime_evening_attendance.isin([0, 1]).all():
        raise ValueError("Kode program studi atau waktu kuliah tidak dikenal.")
    for col in ["Previous_qualification_grade", "Admission_grade"]:
        if not x[col].between(0, 200).all():
            raise ValueError("Nilai masuk/kualifikasi harus berada pada skala 0–200.")
    if not x[SEM+"grade"].between(0,20).all():
        raise ValueError("Rata-rata nilai semester harus berada pada skala 0–20.")
    for col in [c for c in FEATURES if c.startswith(SEM) and c != SEM+"grade"]:
        if (x[col] < 0).any() or (x[col] % 1 != 0).any():
            raise ValueError("Jumlah unit/evaluasi harus berupa bilangan bulat nonnegatif.")
    # Credited units can produce approved > enrolled in the source; do not reject this.
    return x

def metrics(y, probability, threshold):
    from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score, fbeta_score, balanced_accuracy_score, brier_score_loss, confusion_matrix
    pred = probability >= threshold
    return {"pr_auc_ap":float(average_precision_score(y,probability)), "roc_auc":float(roc_auc_score(y,probability)), "precision":float(precision_score(y,pred,zero_division=0)), "recall":float(recall_score(y,pred,zero_division=0)), "f1":float(f1_score(y,pred,zero_division=0)), "f2":float(fbeta_score(y,pred,beta=2,zero_division=0)), "balanced_accuracy":float(balanced_accuracy_score(y,pred)), "brier":float(brier_score_loss(y,probability)), "confusion_matrix":confusion_matrix(y,pred,labels=[0,1]).tolist(), "flagged":int(pred.sum()), "n":int(len(y))}
