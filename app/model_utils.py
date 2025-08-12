import os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

FEATURES = [
    "map_pool_advantage",
    "r2_advantage",
    "winrate_advantage",
    "recent_form",
    "consistency_advantage",
    "rolling_round_diff",
]

def prepare(df: pd.DataFrame, *, start_date: str = "2023-01-01", train_prop: float = 0.75):
    """Fresh, deterministic prep + time split by date. Never mutates caller data.
    
    Args:
        df: Raw dataframe
        start_date: Keep rows on/after this date (YYYY-MM-DD)
        train_prop: Fraction of earliest dates used for training (0.5–0.9 typical)
    """
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.sort_values("date").reset_index(drop=True)
    if start_date is not None:
        d = d[d["date"] >= pd.Timestamp(start_date)].copy()
    # Time-based split
    q = float(train_prop)
    q = min(max(q, 0.01), 0.99)
    split_date = d["date"].quantile(q)
    train = d[d["date"] <  split_date].copy()
    test  = d[d["date"] >= split_date].copy()
    # Feature matrices (neutral-fill NaNs to 0)
    Xtr = train[FEATURES].copy().fillna(0.0)
    Xte = test[FEATURES].copy().fillna(0.0)
    # Labels (1 for Win, 0 for not Win)
    ytr = (train["result"] == "W").astype(int)
    yte = (test["result"]  == "W").astype(int)
    return dict(df=d, train=train, test=test, Xtr=Xtr, Xte=Xte, ytr=ytr, yte=yte, split_date=split_date, train_prop=q)

def train_model(Xtr, ytr, Xte, yte):
    model = LogisticRegression(solver="lbfgs", max_iter=2000, C=10, random_state=42)
    model.fit(Xtr, ytr)
    train_pred = model.predict(Xtr)
    test_pred  = model.predict(Xte)
    train_acc = accuracy_score(ytr, train_pred)
    test_acc  = accuracy_score(yte,  test_pred)
    metrics = {
        "train_acc": float(train_acc),
        "test_acc": float(test_acc),
        "model_type": "LogisticRegression(lbfgs, C=10, max_iter=2000, random_state=42)",
        "features": FEATURES.copy(),
    }
    return model, metrics

def compute_predictions_df(P: dict, model, metrics: dict) -> pd.DataFrame:
    """Compute predictions for every row in P['df'] and return a single DataFrame."""
    d = P["df"].copy()
    X = d[FEATURES].copy().fillna(0.0)
    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= 0.5).astype(int)

    # Determine split label based on date vs split_date
    split_date = P["split_date"]
    split_label = np.where(d["date"] < split_date, "train", "test")

    out = d.copy()
    out["predicted_proba_win"] = probs
    out["predicted_class"] = preds
    out["split"] = split_label
    out["model"] = metrics.get("model_type", "")
    out["train_accuracy"] = metrics.get("train_acc", None)
    out["test_accuracy"] = metrics.get("test_acc", None)
    out["split_date"] = pd.to_datetime(split_date)

    # Reorder columns for readability
    preferred = ["team_name","opponent","date","result","split",
                 "predicted_proba_win","predicted_class","model",
                 "train_accuracy","test_accuracy","split_date"]
    feat_cols_present = [f for f in FEATURES if f in out.columns]
    other_cols = [c for c in out.columns if c not in preferred + feat_cols_present]
    cols = preferred + feat_cols_present + other_cols
    out = out[cols]
    return out

def save_dataframe_csv(df: pd.DataFrame, filename: str = "all_predictions.csv"):
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return filename, csv_bytes