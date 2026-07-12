"""
STEP 5b - MODELING: FRAUD DETECTION CLASSIFICATION
Nexus Bank Capstone | Team 4

Model: Logistic Regression (baseline, interpretable) + Random Forest
(stronger, handles class imbalance better) — compared side by side, as
good practice for a fraud use case where explainability sometimes matters
to the bank's risk team as much as raw accuracy.

Because fraud is extremely rare (~0.17% of transactions, matching the real
Kaggle dataset's imbalance), plain accuracy is misleading (a model that
predicts "never fraud" would score 99.8% accuracy and be useless). We
report Precision, Recall, F1, and ROC-AUC instead, and use class_weight
="balanced" to compensate.

Train/test split is stratified and time-respecting is not required here
since transactions aren't being used to predict the future — but we still
hold out 25% purely for testing, never touched during training.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, roc_curve,
    confusion_matrix, classification_report
)

ROOT = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(ROOT, "db", "nexus_bank.db")
OUT_DIR = os.path.join(ROOT, "outputs")

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM transactions", conn)
    conn.close()

    feature_cols = [c for c in df.columns if c.startswith("V")] + ["Amount"]
    X = df[feature_cols]
    y = df["Class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    models = {
        "LogisticRegression": LogisticRegression(class_weight="balanced", max_iter=1000),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1
        ),
    }

    results = []
    roc_data = {}
    for name, model in models.items():
        model.fit(X_train_s, y_train)
        proba = model.predict_proba(X_test_s)[:, 1]
        preds = model.predict(X_test_s)

        prec = precision_score(y_test, preds)
        rec = recall_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        auc = roc_auc_score(y_test, proba)
        cm = confusion_matrix(y_test, preds)

        results.append({"model": name, "precision": prec, "recall": rec, "f1": f1, "roc_auc": auc})
        fpr, tpr, _ = roc_curve(y_test, proba)
        roc_data[name] = (fpr, tpr, auc)

        print(f"\n=== {name} ===")
        print(f"Precision: {prec:.3f}  Recall: {rec:.3f}  F1: {f1:.3f}  ROC-AUC: {auc:.3f}")
        print("Confusion matrix [ [TN FP] [FN TP] ]:")
        print(cm)

    res_df = pd.DataFrame(results)
    res_df.to_csv(os.path.join(OUT_DIR, "fraud_model_results.csv"), index=False)

    # Save ROC curve data for plotting
    np.savez(os.path.join(OUT_DIR, "roc_data.npz"),
             **{f"{k}_fpr": v[0] for k, v in roc_data.items()},
             **{f"{k}_tpr": v[1] for k, v in roc_data.items()})

    print("\n" + res_df.to_string(index=False))
