import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("raw_data.csv")

# Drop rows missing key values
df = df.dropna(subset=["events", "launch_speed", "launch_angle"])


df = df.copy()

# Top 10 Most Common At-Bat Events
top_events = df['events'].value_counts().nlargest(10)
plt.figure(figsize=(10, 5))
sns.barplot(x=top_events.values, y=top_events.index, palette="coolwarm")
plt.title("Top 10 Most Common At-Bat Events", fontsize=14)
plt.xlabel("Count", fontsize=12)
plt.ylabel("Event Type", fontsize=12)
plt.tight_layout()
plt.show()

# Launch Speed vs. Launch Angle (Hit Quality) 
# Scatter showing batted ball characteristics by event
plt.figure(figsize=(9, 7))
sns.scatterplot(
    data=df[df['events'].isin(top_events.index)],
    x='launch_angle',
    y='launch_speed',
    hue='events',
    alpha=0.5,
    palette='Spectral'
)
plt.title("Launch Speed vs. Launch Angle — Hit Quality and Event Type", fontsize=14)
plt.xlabel("Launch Angle (degrees)", fontsize=12)
plt.ylabel("Launch Speed (mph)", fontsize=12)
plt.legend(title="Event", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# Correlation Heatmap (for continuous features) ==========
# Focus on selected continuous pitch and hit features
continuous_features = [
    'release_speed', 'pfx_x', 'pfx_z', 'plate_x', 'plate_z',
    'launch_speed', 'launch_angle', 'hit_distance_sc', 'spin_rate_deprecated',
    'release_extension'
]

corr = df[continuous_features].corr()
plt.figure(figsize=(10, 8))
sns.heatmap(corr, cmap='coolwarm', annot=False)
plt.title("Feature Correlation — Pitch and Batted Ball Variables", fontsize=14)
plt.tight_layout()
plt.show()

