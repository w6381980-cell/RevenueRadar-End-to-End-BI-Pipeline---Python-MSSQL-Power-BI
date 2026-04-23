# ============================================================
# churn_model.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   ML model se predict karta hai ki kaun sa customer
#   "churn" karega — matlab dobara order nahi karega.
#
# CHURN LOGIC:
#   Agar customer ne last 90 days mein order nahi kiya
#   toh usse "churned" consider karte hain.
#
# ML MODEL:
#   Random Forest Classifier use karta hai.
#   Features: order count, avg spend, days since last order,
#             favorite category, region
#   Output: churn probability (0 to 1)
#
# RUN: python 04_prediction/churn_model.py
# ============================================================

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, roc_auc_score, accuracy_score
)
from sklearn.preprocessing import LabelEncoder
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import get_engine, CLEANED_TABLE, OUTPUT_DIR

def build_customer_features(df):
    """
    LOGIC:
      Har customer ke liye features banao.
      ML model ko raw transactions nahi — aggregated
      customer-level data chahiye.
    """
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    delivered       = df[df["order_status"] == "Delivered"]
    today           = df["sale_date"].max()

    agg = delivered.groupby("customer_email").agg(
        total_orders      = ("order_id",      "count"),
        total_spent       = ("total_amount",  "sum"),
        avg_order_value   = ("total_amount",  "mean"),
        last_order_date   = ("sale_date",     "max"),
        first_order_date  = ("sale_date",     "min"),
        fav_category      = ("category",      lambda x: x.mode()[0]),
        fav_region        = ("region",        lambda x: x.mode()[0]),
        avg_discount      = ("discount_pct",  "mean"),
    ).reset_index()

    # Days since last order
    agg["days_since_last"] = (today - agg["last_order_date"]).dt.days

    # Customer lifetime (days)
    agg["customer_lifetime"] = (
        agg["last_order_date"] - agg["first_order_date"]
    ).dt.days

    # Purchase frequency (orders per month)
    agg["order_frequency"] = (
        agg["total_orders"] / (agg["customer_lifetime"] / 30 + 1)
    ).round(3)

    # CHURN LABEL:
    # Agar 90 din se order nahi kiya → churn = 1
    CHURN_DAYS = 90
    agg["churned"] = (agg["days_since_last"] >= CHURN_DAYS).astype(int)

    return agg

def train_churn_model(features_df):
    """
    RANDOM FOREST CLASSIFIER:
      - Bahut saare decision trees banata hai
      - Har tree vote karta hai
      - Majority vote = final prediction
      - Isliye zyada accurate aur overfitting kam
    """
    print("🤖 Churn model train ho raha hai...")

    # Categorical columns encode karo
    # LOGIC: ML model numbers samajhta hai, text nahi
    le_cat = LabelEncoder()
    le_reg = LabelEncoder()

    df = features_df.copy()
    df["fav_category_enc"] = le_cat.fit_transform(df["fav_category"])
    df["fav_region_enc"]   = le_reg.fit_transform(df["fav_region"])

    # Features (X) aur Target (y) alag karo
    feature_cols = [
        "total_orders", "total_spent", "avg_order_value",
        "days_since_last", "customer_lifetime", "order_frequency",
        "avg_discount", "fav_category_enc", "fav_region_enc"
    ]
    X = df[feature_cols]
    y = df["churned"]

    # Train-test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Model banao aur train karo
    model = RandomForestClassifier(
        n_estimators = 100,    # 100 trees
        max_depth    = 8,      # Depth limit — overfitting rokne ke liye
        random_state = 42,
        class_weight = "balanced"  # Imbalanced data handle karo
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred      = model.predict(X_test)
    y_prob      = model.predict_proba(X_test)[:, 1]
    accuracy    = round(accuracy_score(y_test, y_pred) * 100, 2)
    roc_auc     = round(roc_auc_score(y_test, y_prob) * 100, 2)

    print(f"\n📊 Model Performance:")
    print(f"  Accuracy : {accuracy}%")
    print(f"  ROC-AUC  : {roc_auc}%  (higher = better, 100% = perfect)")
    print(f"  Train rows: {len(X_train):,} | Test rows: {len(X_test):,}")

    # Feature importance — kaunsa feature zyada important hai
    importance = pd.DataFrame({
        "Feature":   feature_cols,
        "Importance": model.feature_importances_.round(4)
    }).sort_values("Importance", ascending=False)
    print(f"\n🎯 Top Features (jo churn predict karne mein help karte hain):")
    print(importance.head(5).to_string(index=False))

    return model, feature_cols, accuracy, roc_auc

def predict_churn(model, features_df, feature_cols):
    """
    Sare customers ke liye churn probability predict karo.
    """
    le_cat = LabelEncoder()
    le_reg = LabelEncoder()

    df = features_df.copy()
    df["fav_category_enc"] = le_cat.fit_transform(df["fav_category"])
    df["fav_region_enc"]   = le_reg.fit_transform(df["fav_region"])

    probs = model.predict_proba(df[feature_cols])[:, 1]
    df["churn_probability"] = (probs * 100).round(1)

    def risk_label(p):
        if p >= 70: return "🔴 High Risk"
        elif p >= 40: return "🟡 Medium Risk"
        else: return "🟢 Low Risk"

    df["risk_level"] = df["churn_probability"].apply(risk_label)

    return df[["customer_email", "total_orders", "total_spent",
               "days_since_last", "churn_probability",
               "risk_level"]].sort_values("churn_probability",
                                           ascending=False)


if __name__ == "__main__":
    print("🚀 RevenueRadar — Churn Prediction Model")
    print("=" * 55)

    engine     = get_engine()
    df         = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    features   = build_customer_features(df)

    print(f"  Customers: {len(features):,}")
    print(f"  Churned  : {features['churned'].sum():,} "
          f"({features['churned'].mean()*100:.1f}%)")

    model, feat_cols, acc, auc = train_churn_model(features)
    predictions = predict_churn(model, features, feat_cols)

    print(f"\n🔴 High Risk Customers (top 10):")
    print(predictions[predictions["risk_level"]
                       .str.contains("High")].head(10).to_string(index=False))

    # Save predictions
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pred_path = os.path.join(OUTPUT_DIR, "churn_predictions.csv")
    predictions.to_csv(pred_path, index=False)
    print(f"\n✅ Predictions saved: {pred_path}")
    print("➡️  Agla step: python 05_reports/impact_report.py")