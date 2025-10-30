import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# The purpose of this file opposed to dataExplore is to evaluate only the most common outcomes and their correlation to some of the most seemingly influential features. 
# I am currently guessing what features may be most important in determining pitch and at-bat outcomes, so this file is definitely subject to change as we narrow features down.


# === Load Data ===
df = pd.read_csv("raw_data.csv")

print("Dataset shape:", df.shape)

# Select Events as our target column, can worry about specific pitch outcomes later
target_col = "events"

# Limit to top 10 most common event types
# top_events = df[target_col].value_counts().index[:10]
# df = df[df[target_col].isin(top_events)]
# print(f"\nFiltered to top 10 events: {list(top_events)}")

# Summarizing missing values
missing = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
print("\nMissing Values (Top 10):")
print(missing.head(10))

# Basic Distribution of Top 5 Event Outcomes
plt.figure(figsize=(8, 4))
sns.countplot(data=df, y=target_col, order=df[target_col].value_counts().index)
plt.title("Top Event Outcomes")
plt.tight_layout()
plt.show()


# Focusing on interpretable features with likely relationships to event results


# More features to consider: release_pos_z, plate_x, plate_z, pfx_x, pfx_z, bb_type, pitch_name, inning_topbot, bat_score, fld_score


# Recommended 20 features
correlation_features = [
    'release_speed', 'effective_speed', 'release_spin_rate',
    'release_pos_x', 'release_pos_z', 'release_extension',
    'pitch_type', 'events', 'description', 'zone',
    'balls', 'strikes', 'outs_when_up', 'inning',
    'on_3b', 'on_2b', 'on_1b',
    'batter_side', 'pitcher_hand',
    'home_team'  # can drop if not available
]

correlation_features = [f for f in correlation_features if f in df.columns]

df_corr = df[correlation_features].copy()

# Correlation Heatmap (10x10 max) to avoid noise
num_df = df[correlation_features].select_dtypes(include=["float64", "int64"])
if not num_df.empty:
    corr = num_df.corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, cmap="coolwarm", center=0, annot=True, fmt=".2f")
    plt.title("Focused Feature Correlation Heatmap")
    plt.tight_layout()
    plt.show()

selected_features = [
    "release_speed",
    "release_spin_rate",
    "launch_speed",
    "launch_angle",
    "effective_speed",
    "balls",
    "strikes",
    "outs_when_up",
    "inning",
    "zone"
]

selected_features = [f for f in selected_features if f in df.columns]


df_subset = df[selected_features].copy()


# Pitch Type vs Event
if "pitch_type" in df.columns:
    plt.figure(figsize=(10, 5))
    sns.countplot(data=df, x="pitch_type", hue=target_col,
                  order=df["pitch_type"].value_counts().index)
    plt.title("Pitch Type vs Top 5 Events")
    plt.legend(title="Event", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

# Count Context (Balls, Strikes, Outs)
for col in ["balls", "strikes", "outs_when_up"]:
    if col in df.columns:
        plt.figure(figsize=(6, 4))
        sns.countplot(data=df, x=col, hue=target_col)
        plt.title(f"{col.capitalize()} vs Top 5 Events")
        plt.legend(title="Event", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

# Release Speed Impact on Event
if "release_speed" in df.columns:
    plt.figure(figsize=(9, 5))
    sns.boxplot(data=df, x=target_col, y="release_speed", order=top_events)
    plt.title(f"Release Speed by Event (Top 5)")
    plt.tight_layout()
    plt.show()

print("Exploration complete.")
