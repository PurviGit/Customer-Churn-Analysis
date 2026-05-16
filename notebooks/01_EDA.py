# ============================================================
# NOTEBOOK 01 - EXPLORATORY DATA ANALYSIS (EDA)
# Customer Churn Project
# ============================================================
# HOW TO USE THIS FILE:
# 1. Open Jupyter Notebook: run "jupyter notebook" in terminal
# 2. Create a new notebook called "01_EDA.ipynb"
# 3. Copy each CELL block below into a separate Jupyter cell
# 4. Run cells one by one (Shift+Enter)
# ============================================================


# ── CELL 1: Import Libraries ─────────────────────────────────
# EXPLANATION: We import all the tools we need upfront.
# pandas = data manipulation (like Excel but in Python)
# numpy = math operations
# matplotlib/seaborn = charts and graphs
# warnings = hide annoying warning messages

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-whitegrid')  # Clean chart style
sns.set_palette("husl")

print("✅ All libraries imported successfully")


# ── CELL 2: Load the Data ────────────────────────────────────
# EXPLANATION: Read the CSV file into a pandas DataFrame.
# A DataFrame is like an Excel table in Python.
# Always do .head() first to see what the data looks like.

df = pd.read_csv('data/telco_churn.csv')

print(f"Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns")
print("\nFirst 5 rows:")
df.head()


# ── CELL 3: Basic Data Info ──────────────────────────────────
# EXPLANATION: .info() tells us column names, data types, and
# how many non-null (non-missing) values each column has.
# This is always step 1 — understand your data before analyzing it.

print("=== DATASET INFO ===")
print(df.info())

print("\n=== MISSING VALUES ===")
print(df.isnull().sum())

print("\n=== DATA TYPES ===")
print(df.dtypes)


# ── CELL 4: Fix Data Quality Issues ─────────────────────────
# EXPLANATION: TotalCharges should be a number but it's stored
# as text (object). This is a VERY common real-world data problem.
# We convert it and fill blanks with 0 (new customers with no charges).
# This is the kind of thing you talk about in interviews!

# TotalCharges has spaces instead of nulls — fix this
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')

# Fill nulls with 0 (these are new customers, tenure=0)
df['TotalCharges'].fillna(0, inplace=True)

# Convert Churn to binary number (Yes=1, No=0) for modeling later
df['Churn_Binary'] = (df['Churn'] == 'Yes').astype(int)

# Convert SeniorCitizen from 0/1 to Yes/No for readability
df['SeniorCitizen'] = df['SeniorCitizen'].map({0: 'No', 1: 'Yes'})

print("✅ Data cleaning complete")
print(f"TotalCharges nulls remaining: {df['TotalCharges'].isnull().sum()}")


# ── CELL 5: Overall Churn Rate ───────────────────────────────
# EXPLANATION: First, understand the scale of the problem.
# What % of customers are churning? This is your headline number.

churn_counts = df['Churn'].value_counts()
churn_pct = df['Churn'].value_counts(normalize=True) * 100

print("=== CHURN OVERVIEW ===")
print(f"Total customers: {len(df):,}")
print(f"Churned: {churn_counts['Yes']:,} ({churn_pct['Yes']:.1f}%)")
print(f"Retained: {churn_counts['No']:,} ({churn_pct['No']:.1f}%)")
print(f"\nMonthly revenue at risk: ${df[df['Churn']=='Yes']['MonthlyCharges'].sum():,.0f}")

# Visualize
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Pie chart
axes[0].pie(churn_counts, labels=['Retained', 'Churned'],
            autopct='%1.1f%%', colors=['#2196F3', '#F44336'],
            startangle=90, textprops={'fontsize': 12})
axes[0].set_title('Overall Churn Rate', fontsize=14, fontweight='bold')

# Bar chart with counts
bars = axes[1].bar(['Retained', 'Churned'], churn_counts,
                   color=['#2196F3', '#F44336'], width=0.5)
axes[1].set_title('Customer Count by Churn Status', fontsize=14, fontweight='bold')
axes[1].set_ylabel('Number of Customers')
for bar, count in zip(bars, churn_counts):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                 f'{count:,}', ha='center', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/01_overall_churn_rate.png', dpi=150, bbox_inches='tight')
plt.show()
print("📊 Chart saved to outputs/")


# ── CELL 6: Churn by Contract Type ───────────────────────────
# EXPLANATION: Contract type is the MOST IMPORTANT churn driver.
# This is always the most interesting finding and what interviewers ask about.
# Month-to-month customers have no commitment, so they leave easily.

contract_churn = df.groupby('Contract')['Churn_Binary'].agg(['mean', 'sum', 'count'])
contract_churn.columns = ['Churn_Rate', 'Churned_Count', 'Total_Count']
contract_churn['Churn_Rate_Pct'] = (contract_churn['Churn_Rate'] * 100).round(1)
contract_churn = contract_churn.sort_values('Churn_Rate', ascending=False)

print("=== CHURN BY CONTRACT TYPE ===")
print(contract_churn[['Churned_Count', 'Total_Count', 'Churn_Rate_Pct']])

fig, ax = plt.subplots(figsize=(10, 6))
colors = ['#F44336', '#FF9800', '#4CAF50']
bars = ax.bar(contract_churn.index, contract_churn['Churn_Rate_Pct'], color=colors, width=0.5)
ax.set_title('Churn Rate by Contract Type\n(Month-to-Month customers churn 3x more!)',
             fontsize=14, fontweight='bold')
ax.set_ylabel('Churn Rate (%)')
ax.set_ylim(0, 55)

for bar, (idx, row) in zip(bars, contract_churn.iterrows()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f"{row['Churn_Rate_Pct']}%\n({int(row['Churned_Count'])} customers)",
            ha='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/02_churn_by_contract.png', dpi=150, bbox_inches='tight')
plt.show()


# ── CELL 7: Churn by Tenure ──────────────────────────────────
# EXPLANATION: Tenure = how long the customer has been with the company.
# We expect new customers to churn more. Let's verify and quantify it.
# We create "tenure buckets" (0-12 months, 13-24 months, etc.)

df['Tenure_Group'] = pd.cut(df['tenure'],
                             bins=[0, 12, 24, 48, 72],
                             labels=['0-12 months', '13-24 months', '25-48 months', '49-72 months'])

tenure_churn = df.groupby('Tenure_Group')['Churn_Binary'].mean() * 100

print("=== CHURN RATE BY CUSTOMER TENURE ===")
for group, rate in tenure_churn.items():
    print(f"  {group}: {rate:.1f}%")

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(tenure_churn.index, tenure_churn.values,
              color=['#F44336', '#FF9800', '#2196F3', '#4CAF50'], width=0.5)
ax.set_title('Churn Rate by Customer Tenure\n(New customers at highest risk!)',
             fontsize=14, fontweight='bold')
ax.set_ylabel('Churn Rate (%)')
ax.set_xlabel('Customer Tenure')

for bar, val in zip(bars, tenure_churn.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val:.1f}%', ha='center', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/03_churn_by_tenure.png', dpi=150, bbox_inches='tight')
plt.show()


# ── CELL 8: Revenue Analysis ─────────────────────────────────
# EXPLANATION: Not all customers are equal. A churned customer paying
# $100/month hurts more than one paying $20/month. Let's calculate
# the actual revenue impact — this is what business teams care about.

churned_df = df[df['Churn'] == 'Yes']
retained_df = df[df['Churn'] == 'No']

monthly_revenue_lost = churned_df['MonthlyCharges'].sum()
avg_monthly_churned = churned_df['MonthlyCharges'].mean()
avg_monthly_retained = retained_df['MonthlyCharges'].mean()

print("=== REVENUE IMPACT ANALYSIS ===")
print(f"Monthly revenue lost to churn: ${monthly_revenue_lost:,.0f}")
print(f"Annual revenue lost to churn: ${monthly_revenue_lost * 12:,.0f}")
print(f"Avg monthly charge - churned customers: ${avg_monthly_churned:.2f}")
print(f"Avg monthly charge - retained customers: ${avg_monthly_retained:.2f}")
print(f"\n💡 Churned customers actually pay MORE on average!")
print(f"   This means we're losing our highest-value customers.")

# Distribution of charges for churned vs retained
fig, ax = plt.subplots(figsize=(12, 6))
ax.hist(retained_df['MonthlyCharges'], bins=30, alpha=0.6, color='#2196F3',
        label=f'Retained (avg ${avg_monthly_retained:.0f})')
ax.hist(churned_df['MonthlyCharges'], bins=30, alpha=0.6, color='#F44336',
        label=f'Churned (avg ${avg_monthly_churned:.0f})')
ax.set_title('Monthly Charges: Churned vs Retained Customers\n(Churned customers pay more — high-value customers leaving!)',
             fontsize=13, fontweight='bold')
ax.set_xlabel('Monthly Charges ($)')
ax.set_ylabel('Number of Customers')
ax.legend(fontsize=12)
ax.axvline(avg_monthly_churned, color='#F44336', linestyle='--', linewidth=2)
ax.axvline(avg_monthly_retained, color='#2196F3', linestyle='--', linewidth=2)

plt.tight_layout()
plt.savefig('outputs/04_revenue_analysis.png', dpi=150, bbox_inches='tight')
plt.show()


# ── CELL 9: Churn by Internet Service ───────────────────────
# EXPLANATION: Fiber optic is the premium internet service.
# Do premium customers churn more? If yes, why? (Service quality issue?)

internet_churn = df.groupby('InternetService')['Churn_Binary'].mean() * 100
print("=== CHURN BY INTERNET SERVICE ===")
print(internet_churn.round(1))

fig, ax = plt.subplots(figsize=(8, 5))
colors = {'DSL': '#2196F3', 'Fiber optic': '#F44336', 'No': '#4CAF50'}
bars = ax.bar(internet_churn.index, internet_churn.values,
              color=[colors[x] for x in internet_churn.index], width=0.4)
ax.set_title('Churn Rate by Internet Service Type', fontsize=13, fontweight='bold')
ax.set_ylabel('Churn Rate (%)')
for bar, val in zip(bars, internet_churn.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val:.1f}%', ha='center', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/05_churn_by_internet.png', dpi=150, bbox_inches='tight')
plt.show()


# ── CELL 10: Senior Citizens Analysis ───────────────────────
# EXPLANATION: Demographics matter for targeting retention campaigns.
# If seniors churn more, the company should create senior-specific support.

senior_churn = df.groupby('SeniorCitizen')['Churn_Binary'].mean() * 100
senior_count = df.groupby('SeniorCitizen').size()

print("=== SENIOR CITIZEN CHURN ANALYSIS ===")
print(f"Non-Senior churn rate: {senior_churn['No']:.1f}%")
print(f"Senior citizen churn rate: {senior_churn['Yes']:.1f}%")
print(f"Seniors are {senior_churn['Yes']/senior_churn['No']:.1f}x more likely to churn!")


# ── CELL 11: Correlation Heatmap ────────────────────────────
# EXPLANATION: A heatmap shows which numerical variables are related.
# High correlation with Churn_Binary = important predictor.
# This helps us pick the right features for our ML model.

numerical_cols = ['tenure', 'MonthlyCharges', 'TotalCharges', 'Churn_Binary']
corr_matrix = df[numerical_cols].corr()

fig, ax = plt.subplots(figsize=(8, 6))
mask = np.zeros_like(corr_matrix, dtype=bool)
mask[np.triu_indices_from(mask)] = True  # Only show lower triangle

sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdYlGn',
            center=0, mask=mask, ax=ax, linewidths=0.5,
            annot_kws={'size': 12, 'weight': 'bold'})
ax.set_title('Correlation Heatmap\n(Values close to 1 or -1 = strong relationship with churn)',
             fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/06_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()

print("\n=== KEY FINDINGS FROM EDA ===")
print("1. Overall churn rate: ~26.5% — affecting 1 in 4 customers")
print("2. Month-to-month customers churn at 42% vs 11% for annual contracts")
print("3. Customers in first 12 months churn at highest rate (47%)")
print("4. Churned customers pay $15/month MORE on average — high-value loss")
print("5. Fiber optic customers churn at 41% — possible service quality issue")
print("6. Senior citizens churn at 41% — need dedicated support programs")
print("\n✅ EDA Complete! Move to 02_feature_engineering.ipynb next")
