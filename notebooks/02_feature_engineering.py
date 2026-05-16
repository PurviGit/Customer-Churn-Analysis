# ============================================================
# NOTEBOOK 02 - FEATURE ENGINEERING & PREPROCESSING
# Customer Churn Project
# ============================================================
# WHAT IS FEATURE ENGINEERING?
# ML models only understand numbers. This notebook converts
# text columns (like "Yes"/"No", "Male"/"Female") into numbers
# and creates new useful columns from existing ones.
# This is one of the most important skills for a data analyst.
# ============================================================


# ── CELL 1: Load Clean Data ──────────────────────────────────

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Load data
df = pd.read_csv('data/telco_churn.csv')

# Apply same fixes from EDA notebook
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['Churn_Binary'] = (df['Churn'] == 'Yes').astype(int)
df['SeniorCitizen'] = df['SeniorCitizen'].map({0: 'No', 1: 'Yes'})

print(f"✅ Data loaded: {df.shape[0]} rows × {df.shape[1]} columns")


# ── CELL 2: Drop Unnecessary Columns ────────────────────────
# EXPLANATION: customerID is just an identifier, not a predictor.
# The original 'Churn' (Yes/No text) is replaced by Churn_Binary (0/1).

df_model = df.drop(columns=['customerID', 'Churn'])
print(f"After dropping ID and original Churn: {df_model.shape[1]} columns remain")


# ── CELL 3: Create New Features ─────────────────────────────
# EXPLANATION: "Feature engineering" means creating NEW columns from existing ones.
# These new columns often capture patterns better than raw columns.
# This shows interviewers you understand the business, not just the data.

# Feature 1: Average monthly spend (Total ÷ months)
# Why? A customer paying $80/month for 10 months is different from
# one paying $80/month for 60 months. This captures value trend.
df_model['AvgMonthlySpend'] = df_model.apply(
    lambda row: row['TotalCharges'] / row['tenure'] if row['tenure'] > 0 else 0, axis=1
)

# Feature 2: Number of additional services the customer uses
# Why? Customers using more services are more "locked in" and less likely to churn
service_cols = ['PhoneService', 'OnlineSecurity', 'OnlineBackup',
                'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies']
df_model['NumServices'] = df_model[service_cols].apply(
    lambda row: sum(1 for val in row if val == 'Yes'), axis=1
)

# Feature 3: Tenure bucket (new vs established customer)
# Why? Churn risk is very different by tenure stage
df_model['TenureBucket'] = pd.cut(df_model['tenure'],
                                    bins=[0, 12, 24, 48, 72],
                                    labels=['New', 'Growing', 'Established', 'Loyal'])

# Feature 4: Is high-value customer? (above median monthly charges)
median_charge = df_model['MonthlyCharges'].median()
df_model['IsHighValue'] = (df_model['MonthlyCharges'] > median_charge).astype(int)

print("✅ New features created:")
print(f"   - AvgMonthlySpend (avg: ${df_model['AvgMonthlySpend'].mean():.2f})")
print(f"   - NumServices (avg: {df_model['NumServices'].mean():.1f})")
print(f"   - TenureBucket (4 groups)")
print(f"   - IsHighValue (1=above median ${median_charge:.0f})")


# ── CELL 4: Check NumServices vs Churn ──────────────────────
# EXPLANATION: Let's verify our new feature is useful —
# do customers with more services actually churn less?

services_churn = df_model.groupby('NumServices')['Churn_Binary'].mean() * 100
print("\n=== CHURN RATE BY NUMBER OF SERVICES ===")
print(services_churn.round(1))
print("\n💡 More services = lower churn (customers are more 'locked in')")


# ── CELL 5: Encode Categorical Variables ────────────────────
# EXPLANATION: ML models need NUMBERS, not text.
# Binary columns (Yes/No) → map to 1/0
# Multi-value columns → use pd.get_dummies (One-Hot Encoding)

# Step 1: Map binary Yes/No columns to 1/0
binary_cols = ['Partner', 'Dependents', 'PhoneService', 'PaperlessBilling',
               'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
               'TechSupport', 'StreamingTV', 'StreamingMovies', 'SeniorCitizen']

for col in binary_cols:
    df_model[col] = df_model[col].map({'Yes': 1, 'No': 0, 'No internet service': 0, 'No phone service': 0})

print("✅ Binary columns encoded (Yes=1, No=0)")
print(f"   Columns encoded: {binary_cols}")


# ── CELL 6: One-Hot Encode Multi-Value Columns ──────────────
# EXPLANATION: Columns like 'Contract' have 3 values:
# Month-to-month, One year, Two year.
# We CAN'T just map these to 1, 2, 3 because that implies
# "Two year" = 3x "Month-to-month" which is wrong.
# One-hot encoding creates separate 0/1 columns for each value.

multi_cols = ['gender', 'MultipleLines', 'InternetService',
              'Contract', 'PaymentMethod', 'TenureBucket']

df_model = pd.get_dummies(df_model, columns=multi_cols, drop_first=True)

print(f"✅ One-hot encoding complete")
print(f"   Final dataset shape: {df_model.shape[0]} rows × {df_model.shape[1]} columns")


# ── CELL 7: Remove Any Remaining Non-Numeric Columns ────────

non_numeric = df_model.select_dtypes(include=['object', 'category']).columns.tolist()
if non_numeric:
    print(f"Dropping remaining non-numeric columns: {non_numeric}")
    df_model = df_model.drop(columns=non_numeric)

print(f"✅ All columns are now numeric. Shape: {df_model.shape}")


# ── CELL 8: Split Features and Target ───────────────────────
# EXPLANATION: X = input features (everything except Churn_Binary)
#              y = target (what we want to predict = Churn_Binary)
# We split 80% for training the model, 20% for testing it.
# random_state=42 ensures the same split every time you run it.

X = df_model.drop(columns=['Churn_Binary'])
y = df_model['Churn_Binary']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
# stratify=y ensures the 80/20 split preserves the same churn ratio

print("=== DATA SPLIT ===")
print(f"Training set: {X_train.shape[0]} customers")
print(f"Testing set:  {X_test.shape[0]} customers")
print(f"Training churn rate: {y_train.mean()*100:.1f}%")
print(f"Testing churn rate:  {y_test.mean()*100:.1f}%")


# ── CELL 9: Scale Numerical Features ────────────────────────
# EXPLANATION: StandardScaler makes all numbers on the same scale.
# Without this, 'tenure' (0-72) would dominate over 'IsHighValue' (0-1)
# because it's much larger, even though both are equally important.
# IMPORTANT: Fit scaler on training data ONLY, then transform both.
# (If you fit on test data too, you're "cheating" — using future info)

scaler = StandardScaler()

num_cols = ['tenure', 'MonthlyCharges', 'TotalCharges', 'AvgMonthlySpend', 'NumServices']
num_cols_present = [c for c in num_cols if c in X_train.columns]

X_train_scaled = X_train.copy()
X_test_scaled = X_test.copy()

X_train_scaled[num_cols_present] = scaler.fit_transform(X_train[num_cols_present])
X_test_scaled[num_cols_present] = scaler.transform(X_test[num_cols_present])

print("\n✅ Scaling complete")
print(f"   Scaled columns: {num_cols_present}")


# ── CELL 10: Save Processed Data ────────────────────────────
# EXPLANATION: Save the processed data so the modeling notebook
# can load it directly without repeating all these steps.

X_train_scaled.to_csv('data/X_train.csv', index=False)
X_test_scaled.to_csv('data/X_test.csv', index=False)
y_train.to_csv('data/y_train.csv', index=False)
y_test.to_csv('data/y_test.csv', index=False)

# Also save feature names (useful for feature importance chart)
feature_names = list(X_train.columns)
pd.Series(feature_names).to_csv('data/feature_names.csv', index=False)

print("\n✅ All processed data saved to /data/ folder")
print(f"   Features: {len(feature_names)} columns")
print("\n🔜 Ready for 03_modeling.ipynb!")
