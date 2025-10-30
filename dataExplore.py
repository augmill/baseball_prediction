# data_exploration.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load your data
file = "raw_data.csv"
df = pd.read_csv(file)

# Display basic structure
print("Dataset shape:", df.shape)
# print("\nColumns:\n", df.columns.tolist())
print("\nSample rows:\n", df.head())

# --- 1. Missing Values Overview ---
print("\nMissing Values (%):")
print((df.isnull().sum() / len(df) * 100).sort_values(ascending=False).head(20))

# --- 2. Target / Outcome Overview ---
# Assume outcome variable could be 'events' or 'description'
target_col = "events"
print(f"\nOutcome distribution ({target_col}):")
print(df[target_col].value_counts(normalize=True).head(20))

plt.figure(figsize=(10, 5))
sns.countplot(data=df, y=target_col, order=df[target_col].value_counts().index[:10])
plt.title(f"Top 10 {target_col} outcomes")
plt.tight_layout()
plt.show()

# --- 3. Pitch Type Analysis ---
if "pitch_type" in df.columns:
    plt.figure(figsize=(10, 5))
    sns.countplot(data=df, x="pitch_type", order=df["pitch_type"].value_counts().index)
    plt.title("Pitch Type Distribution")
    plt.tight_layout()
    plt.show()

    # Pitch type vs outcome
    plt.figure(figsize=(12, 6))
    sns.countplot(data=df, x="pitch_type", hue=target_col,
                  order=df["pitch_type"].value_counts().index)
    plt.title(f"Pitch Type vs {target_col}")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

# --- 4. Count-Based Features ---
for col in ["balls", "strikes", "outs_when_up"]:
    if col in df.columns:
        plt.figure(figsize=(7, 4))
        sns.countplot(data=df, x=col, hue=target_col)
        plt.title(f"{col.capitalize()} vs {target_col}")
        plt.tight_layout()
        plt.show()

# --- 5. Release Speed Impact (if available) ---
if "release_speed" in df.columns:
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=df, x=target_col, y="release_speed")
    plt.title(f"Release Speed by {target_col}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# --- 6. Correlation Heatmap (Numerical Only) ---
num_df = df.select_dtypes(include=["float64", "int64"])
if not num_df.empty:
    corr = num_df.corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, cmap="coolwarm", center=0)
    plt.title("Feature Correlation Heatmap")
    plt.tight_layout()
    plt.show()
