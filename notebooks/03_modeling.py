# ============================================================
# NOTEBOOK 03 - MACHINE LEARNING MODEL BUILDING & EVALUATION
# Customer Churn Project
# ============================================================
# WHAT THIS NOTEBOOK DOES:
# Trains 3 different ML models, compares them, picks the best one,
# evaluates it properly, and creates visualizations for the resume.
# ============================================================


# ── CELL 1: Import Libraries ─────────────────────────────────

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ML models
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

# Evaluation metrics
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, roc_auc_score,
                             roc_curve, precision_recall_curve)

print("✅ Libraries imported")


# ── CELL 2: Load Processed Data ─────────────────────────────
# EXPLANATION: We load the data saved by the feature engineering notebook.
# No need to redo all that preprocessing.

X_train = pd.read_csv('data/X_train.csv')
X_test = pd.read_csv('data/X_test.csv')
y_train = pd.read_csv('data/y_train.csv').squeeze()
y_test = pd.read_csv('data/y_test.csv').squeeze()
feature_names = pd.read_csv('data/feature_names.csv').squeeze().tolist()

print(f"✅ Data loaded")
print(f"   Training: {X_train.shape[0]} customers, {X_train.shape[1]} features")
print(f"   Testing:  {X_test.shape[0]} customers")


# ── CELL 3: Train 3 Models ───────────────────────────────────
# EXPLANATION:
# Model 1 - Logistic Regression: Simple, interpretable, good baseline
# Model 2 - Random Forest: Ensemble of decision trees, usually more accurate
# Model 3 - Gradient Boosting: Best accuracy, industry standard for tabular data
#
# WHY 3 MODELS? Because you never know which one will be best on your data.
# Train all, compare, pick the winner. This shows analytical thinking!

models = {
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
}

results = {}

print("Training models...")
for name, model in models.items():
    # Train model
    model.fit(X_train, y_train)

    # Predict on test set
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]  # probability of churn

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)

    # False positive rate: How often we wrongly predict churn (wastes retention budget)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    false_positive_rate = fp / (fp + tn)

    results[name] = {
        'model': model,
        'y_pred': y_pred,
        'y_prob': y_prob,
        'accuracy': accuracy,
        'roc_auc': roc_auc,
        'false_positive_rate': false_positive_rate
    }

    print(f"\n{name}:")
    print(f"  Accuracy:           {accuracy*100:.1f}%")
    print(f"  ROC-AUC Score:      {roc_auc:.3f}")
    print(f"  False Positive Rate:{false_positive_rate*100:.1f}%")


# ── CELL 4: Model Comparison Chart ──────────────────────────
# EXPLANATION: Visualize which model performs best.
# ROC-AUC = Area Under the Curve — higher is better (max=1.0, random=0.5)
# It measures how well the model separates churners from non-churners.

metrics_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Accuracy (%)': [r['accuracy']*100 for r in results.values()],
    'ROC-AUC': [r['roc_auc'] for r in results.values()],
    'False Positive Rate (%)': [r['false_positive_rate']*100 for r in results.values()]
})

print("\n=== MODEL COMPARISON ===")
print(metrics_df.to_string(index=False))

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
colors = ['#2196F3', '#FF9800', '#4CAF50']

for i, (metric, title) in enumerate([
    ('Accuracy (%)', 'Accuracy (%)'),
    ('ROC-AUC', 'ROC-AUC Score (Higher = Better)'),
    ('False Positive Rate (%)', 'False Positive Rate % (Lower = Better)')
]):
    bars = axes[i].bar(metrics_df['Model'], metrics_df[metric], color=colors, width=0.5)
    axes[i].set_title(title, fontsize=12, fontweight='bold')
    axes[i].set_ylim(0, max(metrics_df[metric]) * 1.2)
    if 'Rate' in metric and 'False' in metric:
        axes[i].set_ylim(0, 30)
    for bar, val in zip(bars, metrics_df[metric]):
        axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                     f'{val:.1f}', ha='center', fontsize=11, fontweight='bold')
    axes[i].tick_params(axis='x', rotation=15)

plt.tight_layout()
plt.savefig('outputs/07_model_comparison.png', dpi=150, bbox_inches='tight')
plt.show()


# ── CELL 5: Evaluate Best Model — Random Forest ──────────────
# EXPLANATION: Random Forest is usually the best balance of accuracy
# and interpretability. Let's do a deep evaluation on it.

best_model_name = 'Random Forest'
best_result = results[best_model_name]
best_model = best_result['model']

print(f"\n=== DEEP EVALUATION: {best_model_name} ===")
print("\nClassification Report:")
print(classification_report(y_test, best_result['y_pred'],
                             target_names=['Retained', 'Churned']))

# EXPLAIN CLASSIFICATION REPORT:
# Precision: Of customers we predicted churn, what % actually churned?
# Recall: Of all customers who actually churned, what % did we catch?
# F1-Score: Balance of precision and recall
# Support: How many customers in each category


# ── CELL 6: Confusion Matrix ─────────────────────────────────
# EXPLANATION: Shows exactly where the model gets it right and wrong.
# True Positive (TP): Predicted churn, actually churned ✅
# True Negative (TN): Predicted no churn, didn't churn ✅
# False Positive (FP): Predicted churn, but customer stayed ❌ (wastes budget)
# False Negative (FN): Predicted no churn, but customer left ❌ (missed opportunity)

cm = confusion_matrix(y_test, best_result['y_pred'])
tn, fp, fn, tp = cm.ravel()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Heatmap
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Predicted: Retained', 'Predicted: Churned'],
            yticklabels=['Actual: Retained', 'Actual: Churned'],
            ax=axes[0], linewidths=0.5, annot_kws={'size': 14, 'weight': 'bold'})
axes[0].set_title(f'Confusion Matrix — {best_model_name}', fontsize=13, fontweight='bold')

# Business impact interpretation
labels = ['Correct\nRetained\n(True Neg)', 'Wrong\nAlert\n(False Pos)',
          'Missed\nChurner\n(False Neg)', 'Correct\nChurner\n(True Pos)']
values = [tn, fp, fn, tp]
colors = ['#4CAF50', '#FF9800', '#F44336', '#2196F3']
bars = axes[1].bar(labels, values, color=colors, width=0.5)
axes[1].set_title('Business Impact of Predictions', fontsize=13, fontweight='bold')
axes[1].set_ylabel('Number of Customers')
for bar, val in zip(bars, values):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                 str(val), ha='center', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/08_confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\nBusiness interpretation:")
print(f"  ✅ Correctly identified {tp} churners we can save")
print(f"  ❌ Missed {fn} churners (false negatives)")
print(f"  ⚠️  Wasted retention effort on {fp} customers who wouldn't churn anyway")


# ── CELL 7: ROC Curve ────────────────────────────────────────
# EXPLANATION: ROC Curve shows model performance at ALL thresholds.
# Default threshold is 0.5 — but you can adjust it.
# Lower threshold = catch more churners (but more false positives)
# Higher threshold = fewer false alarms (but miss more churners)
# AUC = area under this curve. Higher AUC = better model.

fig, ax = plt.subplots(figsize=(8, 6))
colors_roc = {'Logistic Regression': '#2196F3', 'Random Forest': '#4CAF50',
               'Gradient Boosting': '#FF9800'}

for name, result in results.items():
    fpr, tpr, _ = roc_curve(y_test, result['y_prob'])
    ax.plot(fpr, tpr, lw=2, label=f"{name} (AUC={result['roc_auc']:.3f})",
            color=colors_roc[name])

ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Random classifier (AUC=0.500)')
ax.set_xlabel('False Positive Rate (Type I Error)', fontsize=12)
ax.set_ylabel('True Positive Rate (Recall)', fontsize=12)
ax.set_title('ROC Curve — Model Comparison\n(Closer to top-left = better)',
             fontsize=13, fontweight='bold')
ax.legend(loc='lower right', fontsize=11)
ax.fill_between(*roc_curve(y_test, results['Random Forest']['y_prob'])[:2],
                alpha=0.1, color='#4CAF50')

plt.tight_layout()
plt.savefig('outputs/09_roc_curve.png', dpi=150, bbox_inches='tight')
plt.show()


# ── CELL 8: Feature Importance ───────────────────────────────
# EXPLANATION: Which columns/features does the model rely on most?
# This tells you WHAT DRIVES CHURN — the most business-relevant output.
# You can directly tell the business: "These 5 things predict churn."

importances = best_model.feature_importances_
feature_importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Importance': importances
}).sort_values('Importance', ascending=False).head(15)

fig, ax = plt.subplots(figsize=(10, 8))
bars = ax.barh(feature_importance_df['Feature'][::-1],
               feature_importance_df['Importance'][::-1],
               color='#2196F3')
ax.set_title('Top 15 Features Driving Customer Churn\n(Random Forest Feature Importance)',
             fontsize=13, fontweight='bold')
ax.set_xlabel('Importance Score')

for bar, val in zip(bars, feature_importance_df['Importance'][::-1]):
    ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
            f'{val:.3f}', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('outputs/10_feature_importance.png', dpi=150, bbox_inches='tight')
plt.show()

print("Top 5 churn drivers:")
for i, row in feature_importance_df.head(5).iterrows():
    print(f"  {row['Feature']}: {row['Importance']:.3f}")


# ── CELL 9: Business Simulation — Retention Campaign ────────
# EXPLANATION: THIS IS THE MOST IMPORTANT CELL.
# We use the model to identify the highest-risk customers AND calculate
# how much money a targeted retention campaign could save.
# This is what you present to business stakeholders.

# Reload original data to get actual customer info back
df_orig = pd.read_csv('data/telco_churn.csv')
df_orig['TotalCharges'] = pd.to_numeric(df_orig['TotalCharges'], errors='coerce').fillna(0)
df_orig['Churn_Binary'] = (df_orig['Churn'] == 'Yes').astype(int)

# Get churn probabilities for TEST set customers
churn_probs = best_result['y_prob']

# Create risk ranking dataframe
test_indices = y_test.index
risk_df = df_orig.loc[test_indices, ['tenure', 'MonthlyCharges', 'Contract', 'InternetService']].copy()
risk_df['Churn_Probability'] = (churn_probs * 100).round(1)
risk_df['Risk_Level'] = pd.cut(risk_df['Churn_Probability'],
                                bins=[0, 30, 60, 100],
                                labels=['Low Risk', 'Medium Risk', 'High Risk'])
risk_df['Monthly_Revenue'] = risk_df['MonthlyCharges']
risk_df = risk_df.sort_values('Churn_Probability', ascending=False)

# Calculate campaign impact
high_risk = risk_df[risk_df['Risk_Level'] == 'High Risk']
medium_risk = risk_df[risk_df['Risk_Level'] == 'Medium Risk']

print("=== RETENTION CAMPAIGN SIMULATION ===\n")
print(f"High Risk customers:   {len(high_risk):,} customers")
print(f"Revenue at risk:       ${high_risk['Monthly_Revenue'].sum():,.0f}/month")
print(f"                       ${high_risk['Monthly_Revenue'].sum()*12:,.0f}/year\n")

for retention_rate in [0.10, 0.20, 0.30]:
    saved = high_risk['Monthly_Revenue'].sum() * retention_rate
    print(f"If we retain {retention_rate*100:.0f}% of high-risk customers: "
          f"${saved:,.0f}/month = ${saved*12:,.0f}/year saved")

print(f"\nTop 10 highest-risk customers to contact first:")
print(risk_df.head(10)[['tenure', 'MonthlyCharges', 'Contract', 'Churn_Probability', 'Risk_Level']].to_string())


# ── CELL 10: Save Final Results ──────────────────────────────

risk_df.to_csv('outputs/customer_risk_scores.csv', index=True)

with open('outputs/model_results.txt', 'w') as f:
    f.write("=== CHURN PREDICTION MODEL RESULTS ===\n\n")
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Accuracy: {best_result['accuracy']*100:.1f}%\n")
    f.write(f"ROC-AUC Score: {best_result['roc_auc']:.3f}\n")
    f.write(f"False Positive Rate: {best_result['false_positive_rate']*100:.1f}%\n\n")
    f.write(f"True Positives (Churners caught): {tp}\n")
    f.write(f"False Negatives (Churners missed): {fn}\n")
    f.write(f"False Positives (Wrong alerts): {fp}\n\n")
    f.write("Business Impact:\n")
    f.write(f"High-risk customers identified: {len(high_risk)}\n")
    f.write(f"Monthly revenue at risk: ${high_risk['Monthly_Revenue'].sum():,.0f}\n")
    f.write(f"Potential annual savings (20% retention): ${high_risk['Monthly_Revenue'].sum()*0.20*12:,.0f}\n")

print("\n✅ All outputs saved!")
print("   - outputs/customer_risk_scores.csv")
print("   - outputs/model_results.txt")
print("   - outputs/07 to 10 - Charts saved")
print("\n🎉 PROJECT COMPLETE! Now build your Power BI dashboard using dashboard/dashboard_guide.md")
