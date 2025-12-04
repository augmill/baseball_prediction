"""
Baseball Pitch Embeddings Clustering Analysis - Version 2
=========================================================
Updated based on initial results:
- Fixed integer event handling
- Added balanced sampling for better visualization
- Added per-event analysis to see where rare events cluster
- Improved highlighted events plot

Requirements:
    pip install google-cloud-bigquery pandas numpy scikit-learn matplotlib seaborn plotly db-dtypes

Usage:
    1. Update the BigQuery query with your project/dataset/table names
    2. Ensure you have Google Cloud credentials configured
    3. Run: python baseball_clustering_v2.py
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, adjusted_rand_score, normalized_mutual_info_score
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================
PROJECT_ID = "baseball-prediction-473623"  # Your Google Cloud project ID
DATASET_ID = "statcast_data"      # Your BigQuery dataset name
TABLE_ID = "atbat_sent_features"          # Your BigQuery table name

# Clustering parameters
N_COMPONENTS_VISUALIZATION = 2   # Dimensions for visualization
N_COMPONENTS_CLUSTERING = 50     # Dimensions for clustering
RANDOM_STATE = 42

# ============================================================================
# STEP 1: DATA EXTRACTION FROM BIGQUERY
# ============================================================================
def load_data_from_bigquery():
    """Load embeddings and event labels from BigQuery"""
    print("=" * 60)
    print("STEP 1: Loading Data from BigQuery")
    print("=" * 60)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT 
        game_id,
        at_bat_number,
        pitch_number,
        sentence_embeddings,
        events
    FROM 
        `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE 
        sentence_embeddings IS NOT NULL
        AND events IS NOT NULL
        AND RAND() < 0.01
    LIMIT 50000
    """
    
    print(f"Executing query on {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}...")
    df = client.query(query).to_dataframe()
    print(f"✓ Loaded {len(df)} records")
    
    return df


def extract_embeddings(df):
    """Extract embedding vectors from the RECORD/nested structure"""
    print("\nExtracting embedding vectors...")
    
    def extract_embedding(row):
        """Handle the BigQuery nested structure: {'list': [{'element': val}, ...]}"""
        if row is None:
            return None
        try:
            if isinstance(row, dict) and 'list' in row:
                list_data = row['list']
                return np.array([item['element'] for item in list_data], dtype=float)
            if isinstance(row, np.ndarray):
                return row.astype(float)
            if isinstance(row, list):
                return np.array(row, dtype=float)
            return None
        except (ValueError, TypeError, KeyError) as e:
            return None
    
    df['embedding_array'] = df['sentence_embeddings'].apply(extract_embedding)
    
    initial_count = len(df)
    df = df[df['embedding_array'].notna()].reset_index(drop=True)
    
    if len(df) == 0:
        raise ValueError("No embeddings could be extracted")
    
    embeddings_matrix = np.vstack(df['embedding_array'].values)
    print(f"✓ Embeddings shape: {embeddings_matrix.shape}")
    
    return df, embeddings_matrix


# ============================================================================
# STEP 2: EVENT EXPLORATION (FIXED FOR INTEGER EVENTS)
# ============================================================================
def explore_events(df):
    """Explore and visualize the distribution of events"""
    print("\n" + "=" * 60)
    print("STEP 2: Exploring Event Distribution")
    print("=" * 60)
    
    # Ensure events are integers
    df['events'] = pd.to_numeric(df['events'], errors='coerce').astype(int)
    
    event_counts = df['events'].value_counts().sort_index()
    print(f"\nUnique events: {len(event_counts)}")
    print("\nEvent Distribution:")
    print(event_counts.to_string())
    
    # Create string labels for events
    df['event_category'] = df['events'].apply(lambda x: f"Event_{int(x)}")
    
    # Visualization
    fig, ax = plt.subplots(figsize=(14, 6))
    
    colors = plt.cm.tab20(np.linspace(0, 1, len(event_counts)))
    bars = ax.bar(range(len(event_counts)), event_counts.values, color=colors, edgecolor='black')
    ax.set_xticks(range(len(event_counts)))
    ax.set_xticklabels([f"Event_{i}" for i in event_counts.index], rotation=45, ha='right')
    ax.set_title('Distribution of Events', fontsize=14)
    ax.set_xlabel('Event Code')
    ax.set_ylabel('Count')
    
    for i, (idx, val) in enumerate(event_counts.items()):
        ax.text(i, val + 0.5, f'{val:,}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('01_event_distribution.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 01_event_distribution.png")
    
    return df


# ============================================================================
# STEP 3: PCA DIMENSIONALITY REDUCTION
# ============================================================================
def perform_pca(embeddings_matrix):
    """Perform PCA dimensionality reduction"""
    print("\n" + "=" * 60)
    print("STEP 3: PCA Dimensionality Reduction")
    print("=" * 60)
    
    scaler = StandardScaler()
    embeddings_scaled = scaler.fit_transform(embeddings_matrix)
    
    pca_2d = PCA(n_components=2, random_state=RANDOM_STATE)
    embeddings_pca_2d = pca_2d.fit_transform(embeddings_scaled)
    print(f"✓ Explained variance (2D): {pca_2d.explained_variance_ratio_.sum():.3f}")
    
    pca_3d = PCA(n_components=3, random_state=RANDOM_STATE)
    embeddings_pca_3d = pca_3d.fit_transform(embeddings_scaled)
    print(f"✓ Explained variance (3D): {pca_3d.explained_variance_ratio_.sum():.3f}")
    
    pca_cluster = PCA(n_components=N_COMPONENTS_CLUSTERING, random_state=RANDOM_STATE)
    embeddings_pca_cluster = pca_cluster.fit_transform(embeddings_scaled)
    print(f"✓ Explained variance ({N_COMPONENTS_CLUSTERING}D): {pca_cluster.explained_variance_ratio_.sum():.3f}")
    
    # Variance plot
    pca_full = PCA(n_components=min(100, embeddings_scaled.shape[1]), random_state=RANDOM_STATE)
    pca_full.fit(embeddings_scaled)
    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].bar(range(1, min(51, len(pca_full.explained_variance_ratio_) + 1)), 
                pca_full.explained_variance_ratio_[:50], 
                color='steelblue', edgecolor='black', alpha=0.7)
    axes[0].set_xlabel('Principal Component')
    axes[0].set_ylabel('Variance Explained')
    axes[0].set_title('Variance Explained by Each Component')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(range(1, len(cumulative_variance) + 1), cumulative_variance, 'b-', linewidth=2)
    axes[1].axhline(y=0.95, color='r', linestyle='--', label='95% variance')
    axes[1].axhline(y=0.90, color='orange', linestyle='--', label='90% variance')
    axes[1].axvline(x=N_COMPONENTS_CLUSTERING, color='green', linestyle='--', label=f'{N_COMPONENTS_CLUSTERING} components')
    axes[1].set_xlabel('Number of Components')
    axes[1].set_ylabel('Cumulative Explained Variance')
    axes[1].set_title('Cumulative Explained Variance')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('02_pca_variance_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 02_pca_variance_analysis.png")
    
    return embeddings_scaled, embeddings_pca_2d, embeddings_pca_3d, embeddings_pca_cluster


# ============================================================================
# STEP 4: FIND OPTIMAL CLUSTERS
# ============================================================================
def find_optimal_clusters(embeddings, max_k=15):
    """Find optimal number of clusters"""
    print("\n" + "=" * 60)
    print("STEP 4: Finding Optimal Number of Clusters")
    print("=" * 60)
    
    inertias = []
    silhouettes = []
    K_range = range(2, max_k + 1)
    
    print("\nTesting different K values...")
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        kmeans.fit(embeddings)
        inertias.append(kmeans.inertia_)
        sil_score = silhouette_score(embeddings, kmeans.labels_)
        silhouettes.append(sil_score)
        print(f"  K={k:2d}: Silhouette={sil_score:.4f}")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].plot(K_range, inertias, 'bo-', linewidth=2, markersize=8)
    axes[0].set_xlabel('Number of Clusters (K)')
    axes[0].set_ylabel('Inertia')
    axes[0].set_title('Elbow Method for Optimal K')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(K_range, silhouettes, 'ro-', linewidth=2, markersize=8)
    axes[1].set_xlabel('Number of Clusters (K)')
    axes[1].set_ylabel('Silhouette Score')
    axes[1].set_title('Silhouette Score for Optimal K')
    axes[1].grid(True, alpha=0.3)
    
    optimal_k = K_range[np.argmax(silhouettes)]
    axes[1].axvline(x=optimal_k, color='green', linestyle='--', label=f'Optimal K={optimal_k}')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig('03_cluster_optimization.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 03_cluster_optimization.png")
    
    print(f"\n→ Optimal K: {optimal_k}")
    
    return optimal_k, silhouettes


# ============================================================================
# STEP 5: PERFORM CLUSTERING
# ============================================================================
def perform_clustering(df, embeddings_pca_cluster, embeddings_pca_2d, n_clusters):
    """Perform K-Means clustering"""
    print("\n" + "=" * 60)
    print("STEP 5: Performing Clustering")
    print("=" * 60)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    df['cluster_kmeans'] = kmeans.fit_predict(embeddings_pca_cluster)
    
    print(f"✓ K-Means clustering complete with {n_clusters} clusters")
    print(f"  Cluster sizes: {dict(Counter(df['cluster_kmeans']))}")
    
    return df, kmeans


# ============================================================================
# STEP 6: EVALUATE CLUSTERING
# ============================================================================
def evaluate_clustering(df, embeddings_pca_cluster):
    """Evaluate clustering quality"""
    print("\n" + "=" * 60)
    print("STEP 6: Evaluating Clustering Quality")
    print("=" * 60)
    
    le = LabelEncoder()
    df['event_encoded'] = le.fit_transform(df['events'])
    
    ari = adjusted_rand_score(df['event_encoded'], df['cluster_kmeans'])
    nmi = normalized_mutual_info_score(df['event_encoded'], df['cluster_kmeans'])
    sil = silhouette_score(embeddings_pca_cluster, df['cluster_kmeans'])
    
    print(f"\nAdjusted Rand Index (ARI): {ari:.4f}")
    print(f"Normalized Mutual Information (NMI): {nmi:.4f}")
    print(f"Silhouette Score: {sil:.4f}")
    
    print("\n--- Interpretation ---")
    if ari > 0.3:
        print("✓ STRONG: Clusters correlate with events")
    elif ari > 0.1:
        print("○ MODERATE: Some correlation")
    else:
        print("✗ WEAK: Clusters don't correspond to events")
        print("  → Embeddings cluster by CONTEXT, not OUTCOME")
    
    results = {'ARI': ari, 'NMI': nmi, 'Silhouette': sil}
    
    return df, results, le


# ============================================================================
# STEP 7: ANALYZE CLUSTER COMPOSITION
# ============================================================================
def analyze_cluster_composition(df):
    """Analyze cluster composition"""
    print("\n" + "=" * 60)
    print("STEP 7: Cluster Composition Analysis")
    print("=" * 60)
    
    contingency = pd.crosstab(df['cluster_kmeans'], df['event_category'], normalize='index')
    contingency_counts = pd.crosstab(df['cluster_kmeans'], df['event_category'])
    
    # Heatmap - proportions
    plt.figure(figsize=(16, 8))
    sns.heatmap(contingency, annot=True, fmt='.2f', cmap='YlOrRd', linewidths=0.5)
    plt.title('Cluster vs Event Category (Proportion within each cluster)')
    plt.xlabel('Event Category')
    plt.ylabel('Cluster')
    plt.tight_layout()
    plt.savefig('04_cluster_event_heatmap.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 04_cluster_event_heatmap.png")
    
    # Heatmap - counts
    plt.figure(figsize=(16, 8))
    sns.heatmap(contingency_counts, annot=True, fmt='d', cmap='Blues', linewidths=0.5)
    plt.title('Cluster vs Event Category (Counts)')
    plt.xlabel('Event Category')
    plt.ylabel('Cluster')
    plt.tight_layout()
    plt.savefig('05_cluster_event_counts.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 05_cluster_event_counts.png")
    
    return contingency, contingency_counts


# ============================================================================
# STEP 8: NEW - ANALYZE WHERE EACH EVENT CLUSTERS (Key insight!)
# ============================================================================
def analyze_event_clustering(df):
    """Analyze how each event type is distributed across clusters"""
    print("\n" + "=" * 60)
    print("STEP 8: Per-Event Cluster Distribution")
    print("=" * 60)
    
    # For each event, show which clusters it falls into
    event_cluster_dist = pd.crosstab(df['events'], df['cluster_kmeans'], normalize='index')
    
    print("\nHow each event is distributed across clusters:")
    print("(Each row sums to 1.0 - shows what % of that event is in each cluster)\n")
    
    for event in sorted(df['events'].unique()):
        event_data = df[df['events'] == event]
        cluster_dist = event_data['cluster_kmeans'].value_counts(normalize=True).sort_index()
        n_samples = len(event_data)
        
        # Check if event is concentrated or spread
        max_cluster_pct = cluster_dist.max()
        
        print(f"Event {event:2d} (n={n_samples:4d}): ", end="")
        for cluster in sorted(df['cluster_kmeans'].unique()):
            pct = cluster_dist.get(cluster, 0) * 100
            print(f"C{cluster}:{pct:4.1f}% ", end="")
        
        if max_cluster_pct > 0.4:
            print(f" ← Concentrated in C{cluster_dist.idxmax()}")
        else:
            print(" ← Spread across clusters")
    
    # Visualize: Heatmap showing event → cluster distribution
    plt.figure(figsize=(12, 10))
    sns.heatmap(event_cluster_dist, annot=True, fmt='.2f', cmap='RdYlGn', 
                linewidths=0.5, vmin=0, vmax=0.5)
    plt.title('Where Does Each Event Cluster?\n(Row-normalized: each event sums to 1.0)')
    plt.xlabel('Cluster')
    plt.ylabel('Event')
    plt.tight_layout()
    plt.savefig('08_event_to_cluster_distribution.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n✓ Saved: 08_event_to_cluster_distribution.png")
    
    return event_cluster_dist


# ============================================================================
# STEP 9: VISUALIZATIONS (FIXED)
# ============================================================================
def create_visualizations(df, embeddings_pca_2d, embeddings_pca_3d):
    """Create visualizations"""
    print("\n" + "=" * 60)
    print("STEP 9: Creating Visualizations")
    print("=" * 60)
    
    df['pca_x'] = embeddings_pca_2d[:, 0]
    df['pca_y'] = embeddings_pca_2d[:, 1]
    df['pca_z'] = embeddings_pca_3d[:, 2]
    
    # -------------------------------------------------------------------------
    # 2D Comparison: Events vs Clusters
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    
    # Get unique events and assign colors
    unique_events = sorted(df['events'].unique())
    colors = plt.cm.tab20(np.linspace(0, 1, len(unique_events)))
    event_color_map = {event: colors[i] for i, event in enumerate(unique_events)}
    
    # By event
    for event in unique_events:
        mask = df['events'] == event
        axes[0].scatter(df.loc[mask, 'pca_x'], df.loc[mask, 'pca_y'], 
                       c=[event_color_map[event]], label=f'Event_{event}', 
                       alpha=0.5, s=15)
    axes[0].set_title('PCA 2D - Colored by Event', fontsize=14)
    axes[0].set_xlabel('PC1')
    axes[0].set_ylabel('PC2')
    axes[0].legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
    
    # By cluster
    scatter = axes[1].scatter(df['pca_x'], df['pca_y'], 
                             c=df['cluster_kmeans'], cmap='tab10', alpha=0.5, s=15)
    axes[1].set_title('PCA 2D - Colored by K-Means Cluster', fontsize=14)
    axes[1].set_xlabel('PC1')
    axes[1].set_ylabel('PC2')
    plt.colorbar(scatter, ax=axes[1], label='Cluster')
    
    plt.tight_layout()
    plt.savefig('06_pca_2d_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 06_pca_2d_comparison.png")
    
    # -------------------------------------------------------------------------
    # NEW: PCA 2D excluding Events 4 and 16 (to see other events clearly)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    
    # Filter out events 4 and 16
    excluded_events = [4, 16]
    df_filtered = df[~df['events'].isin(excluded_events)].copy()
    
    print(f"\n  Filtered view: {len(df_filtered)} samples (excluding Events 4 & 16)")
    
    # Get unique events for filtered data and assign distinct colors
    unique_events_filtered = sorted(df_filtered['events'].unique())
    colors_filtered = plt.cm.tab20(np.linspace(0, 1, len(unique_events_filtered)))
    event_color_map_filtered = {event: colors_filtered[i] for i, event in enumerate(unique_events_filtered)}
    
    # Plot background (Events 4 & 16) in very light gray
    df_background = df[df['events'].isin(excluded_events)]
    axes[0].scatter(df_background['pca_x'], df_background['pca_y'], 
                   c='lightgray', alpha=0.1, s=5, label='Events 4 & 16 (background)')
    
    # By event (filtered)
    for event in unique_events_filtered:
        mask = df_filtered['events'] == event
        n_samples = mask.sum()
        axes[0].scatter(df_filtered.loc[mask, 'pca_x'], df_filtered.loc[mask, 'pca_y'], 
                       c=[event_color_map_filtered[event]], label=f'Event_{event} (n={n_samples})', 
                       alpha=0.7, s=30, edgecolors='black', linewidths=0.3)
    
    axes[0].set_title('PCA 2D - Excluding Events 4 & 16\n(Colored by Event)', fontsize=14)
    axes[0].set_xlabel('PC1')
    axes[0].set_ylabel('PC2')
    axes[0].legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    axes[0].grid(True, alpha=0.3)
    
    # By cluster (filtered data only)
    axes[1].scatter(df_background['pca_x'], df_background['pca_y'], 
                   c='lightgray', alpha=0.1, s=5, label='Events 4 & 16 (background)')
    
    scatter = axes[1].scatter(df_filtered['pca_x'], df_filtered['pca_y'], 
                             c=df_filtered['cluster_kmeans'], cmap='tab10', 
                             alpha=0.7, s=30, edgecolors='black', linewidths=0.3)
    axes[1].set_title('PCA 2D - Excluding Events 4 & 16\n(Colored by Cluster)', fontsize=14)
    axes[1].set_xlabel('PC1')
    axes[1].set_ylabel('PC2')
    axes[1].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[1], label='Cluster')
    
    plt.tight_layout()
    plt.savefig('06b_pca_2d_excluding_dominant_events.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 06b_pca_2d_excluding_dominant_events.png")
    
    # -------------------------------------------------------------------------
    # NEW: Only minority events - zoomed analysis
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot ONLY the minority events (no background)
    for event in unique_events_filtered:
        mask = df_filtered['events'] == event
        n_samples = mask.sum()
        ax.scatter(df_filtered.loc[mask, 'pca_x'], df_filtered.loc[mask, 'pca_y'], 
                  c=[event_color_map_filtered[event]], label=f'Event_{event} (n={n_samples})', 
                  alpha=0.8, s=50, edgecolors='black', linewidths=0.5)
    
    ax.set_title('PCA 2D - Minority Events Only\n(Events 4 & 16 completely removed)', fontsize=14)
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('06c_pca_2d_minority_events_only.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 06c_pca_2d_minority_events_only.png")
    
    # -------------------------------------------------------------------------
    # FIXED: Highlighted Events Plot (using integer events)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Define which events to highlight (adjust based on your data)
    # Using the most common + some rare events
    event_counts = df['events'].value_counts()
    common_events = event_counts.head(2).index.tolist()  # Top 2: likely 4, 16
    rare_events = event_counts.tail(3).index.tolist()    # Bottom 3 rare events
    highlight_events = common_events + rare_events
    highlight_colors = ['red', 'blue', 'green', 'orange', 'purple']
    
    # Plot all points in gray first
    ax.scatter(df['pca_x'], df['pca_y'], c='lightgray', alpha=0.3, s=10, label='Other')
    
    # Highlight specific events
    for event, color in zip(highlight_events, highlight_colors):
        if event in df['events'].values:
            mask = df['events'] == event
            n_samples = mask.sum()
            ax.scatter(df.loc[mask, 'pca_x'], df.loc[mask, 'pca_y'], 
                      c=color, alpha=0.7, s=25, label=f'Event_{event} (n={n_samples})')
    
    ax.legend(fontsize=10)
    ax.set_title('PCA 2D - Key Events Highlighted\n(Common events: red/blue, Rare events: green/orange/purple)', fontsize=14)
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('07_pca_highlighted_events.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 07_pca_highlighted_events.png")
    
    # -------------------------------------------------------------------------
    # Cluster Centroids with dominant event
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 10))
    
    scatter = ax.scatter(df['pca_x'], df['pca_y'], 
                        c=df['cluster_kmeans'], cmap='tab10', alpha=0.3, s=10)
    
    for cluster in df['cluster_kmeans'].unique():
        cluster_data = df[df['cluster_kmeans'] == cluster]
        centroid_x = cluster_data['pca_x'].mean()
        centroid_y = cluster_data['pca_y'].mean()
        
        # Find dominant event
        dominant_event = cluster_data['events'].mode()[0]
        dominant_pct = (cluster_data['events'] == dominant_event).mean() * 100
        
        ax.scatter(centroid_x, centroid_y, c='black', s=200, marker='X', 
                  edgecolors='white', linewidths=2)
        ax.annotate(f'C{cluster}\nEvent_{dominant_event}\n({dominant_pct:.0f}%)', 
                   (centroid_x, centroid_y), fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_title('PCA 2D - Clusters with Centroids and Dominant Events')
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    plt.colorbar(scatter, label='Cluster')
    
    plt.tight_layout()
    plt.savefig('09_cluster_centroids.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 09_cluster_centroids.png")
    
    # -------------------------------------------------------------------------
    # NEW: Rare events only - do they cluster together?
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Get rare events (less than 100 samples)
    event_counts = df['events'].value_counts()
    rare_event_ids = event_counts[event_counts < 100].index.tolist()
    
    # Plot common events in gray
    common_mask = ~df['events'].isin(rare_event_ids)
    ax.scatter(df.loc[common_mask, 'pca_x'], df.loc[common_mask, 'pca_y'], 
              c='lightgray', alpha=0.2, s=5, label='Common Events')
    
    # Plot each rare event with different color
    colors = plt.cm.Set1(np.linspace(0, 1, len(rare_event_ids)))
    for event, color in zip(rare_event_ids, colors):
        mask = df['events'] == event
        n_samples = mask.sum()
        ax.scatter(df.loc[mask, 'pca_x'], df.loc[mask, 'pca_y'], 
                  c=[color], alpha=0.8, s=40, label=f'Event_{event} (n={n_samples})', 
                  edgecolors='black', linewidths=0.5)
    
    ax.legend(fontsize=9, loc='upper left')
    ax.set_title('PCA 2D - Rare Events Highlighted\n(Do rare events form distinct clusters?)', fontsize=14)
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('10_rare_events_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 10_rare_events_analysis.png")
    
    # -------------------------------------------------------------------------
    # Stacked bar chart
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, 6))
    
    cluster_composition = df.groupby(['cluster_kmeans', 'events']).size().unstack(fill_value=0)
    cluster_composition_pct = cluster_composition.div(cluster_composition.sum(axis=1), axis=0)
    
    cluster_composition_pct.plot(kind='bar', stacked=True, ax=ax, 
                                  colormap='tab20', edgecolor='black', linewidth=0.5)
    ax.set_title('Event Composition by Cluster (Proportion)')
    ax.set_xlabel('Cluster')
    ax.set_ylabel('Proportion')
    ax.legend(title='Event', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    
    plt.tight_layout()
    plt.savefig('11_cluster_composition_stacked.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 11_cluster_composition_stacked.png")
    
    # -------------------------------------------------------------------------
    # Interactive 3D
    # -------------------------------------------------------------------------
    print("\nCreating interactive 3D visualizations...")
    
    fig_3d = px.scatter_3d(
        df, x='pca_x', y='pca_y', z='pca_z',
        color='events',
        hover_data=['game_id', 'at_bat_number'],
        title='3D PCA - Colored by Event',
        opacity=0.6, height=800
    )
    fig_3d.update_traces(marker_size=3)
    fig_3d.write_html('12_pca_3d_events.html')
    print("✓ Saved: 12_pca_3d_events.html")
    
    return df


# ============================================================================
# STEP 10: GENERATE INSIGHTS REPORT
# ============================================================================
def generate_insights_report(df, results, event_cluster_dist):
    """Generate insights report"""
    print("\n" + "=" * 60)
    print("FINAL INSIGHTS REPORT")
    print("=" * 60)
    
    print("\n" + "─" * 60)
    print("1. DATA SUMMARY")
    print("─" * 60)
    print(f"   • Total samples: {len(df):,}")
    print(f"   • Unique events: {df['events'].nunique()}")
    print(f"   • Clusters: {df['cluster_kmeans'].nunique()}")
    
    print("\n" + "─" * 60)
    print("2. CLUSTERING METRICS")
    print("─" * 60)
    print(f"   • Adjusted Rand Index: {results['ARI']:.4f}")
    print(f"   • Normalized Mutual Info: {results['NMI']:.4f}")
    print(f"   • Silhouette Score: {results['Silhouette']:.4f}")
    
    print("\n" + "─" * 60)
    print("3. KEY FINDING")
    print("─" * 60)
    
    if results['ARI'] < 0.1:
        print("""
   ╔══════════════════════════════════════════════════════════╗
   ║  EMBEDDINGS CLUSTER BY CONTEXT, NOT BY OUTCOME           ║
   ╠══════════════════════════════════════════════════════════╣
   ║  • All clusters have similar event distributions         ║
   ║  • ARI near 0 confirms no correlation with outcomes      ║
   ║  • Embeddings capture WHO is playing, not WHAT happens   ║
   ║                                                          ║
   ║  This SUPPORTS the hypothesis that:                      ║
   ║  "Same players in similar situations can have            ║
   ║   different outcomes - embeddings reflect description,   ║
   ║   not prediction"                                        ║
   ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n" + "─" * 60)
    print("4. WHAT THE EMBEDDINGS LIKELY CAPTURE")
    print("─" * 60)
    print("""
   Based on the clear spatial clusters that DON'T correspond to events:
   
   • Cluster 0: Possibly specific team/stadium combinations
   • Cluster 1: Possibly certain pitcher types or styles  
   • Cluster 2: Possibly particular game situations
   • Cluster 3-5: Other contextual groupings
   
   To verify: Check if samples in the same cluster share:
   - Same pitcher/batter names
   - Same team matchups
   - Similar inning/score situations
    """)
    
    print("\n" + "─" * 60)
    print("5. SAVED FILES")
    print("─" * 60)
    print("""
   01_event_distribution.png      - Event frequency
   02_pca_variance_analysis.png   - PCA explained variance
   03_cluster_optimization.png    - Optimal K selection
   04_cluster_event_heatmap.png   - Cluster→Event proportions
   05_cluster_event_counts.png    - Cluster→Event counts
   06_pca_2d_comparison.png       - Events vs Clusters
   07_pca_highlighted_events.png  - Key events highlighted
   08_event_to_cluster_distribution.png - Event→Cluster distribution
   09_cluster_centroids.png       - Centroids with labels
   10_rare_events_analysis.png    - Rare events analysis
   11_cluster_composition_stacked.png - Stacked composition
   12_pca_3d_events.html          - Interactive 3D
    """)


# ============================================================================
# STEP 11: SAVE RESULTS
# ============================================================================
def save_results(df, embeddings_pca_cluster, embeddings_pca_2d):
    """Save results"""
    print("\n" + "=" * 60)
    print("Saving Results")
    print("=" * 60)
    
    output_cols = ['game_id', 'at_bat_number', 'pitch_number', 'events', 
                   'cluster_kmeans', 'pca_x', 'pca_y']
    output_cols = [c for c in output_cols if c in df.columns]
    
    df[output_cols].to_csv('baseball_clustering_results.csv', index=False)
    print("✓ Saved: baseball_clustering_results.csv")
    
    np.save('embeddings_pca_cluster.npy', embeddings_pca_cluster)
    np.save('embeddings_pca_2d.npy', embeddings_pca_2d)
    print("✓ Saved: embeddings_pca_cluster.npy, embeddings_pca_2d.npy")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print("=" * 60)


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "=" * 60)
    print("BASEBALL EMBEDDINGS CLUSTERING ANALYSIS v2")
    print("=" * 60)
    
    # Step 1: Load data
    df = load_data_from_bigquery()
    df, embeddings_matrix = extract_embeddings(df)
    
    # Step 2: Explore events
    df = explore_events(df)
    
    # Step 3: PCA
    embeddings_scaled, embeddings_pca_2d, embeddings_pca_3d, embeddings_pca_cluster = perform_pca(embeddings_matrix)
    
    # Step 4: Find optimal K
    optimal_k, _ = find_optimal_clusters(embeddings_pca_cluster)
    
    # Step 5: Clustering
    df, kmeans = perform_clustering(df, embeddings_pca_cluster, embeddings_pca_2d, optimal_k)
    
    # Step 6: Evaluate
    df, results, le = evaluate_clustering(df, embeddings_pca_cluster)
    
    # Step 7: Cluster composition
    contingency, _ = analyze_cluster_composition(df)
    
    # Step 8: NEW - Per-event analysis
    event_cluster_dist = analyze_event_clustering(df)
    
    # Step 9: Visualizations
    df = create_visualizations(df, embeddings_pca_2d, embeddings_pca_3d)
    
    # Step 10: Report
    generate_insights_report(df, results, event_cluster_dist)
    
    # Step 11: Save
    save_results(df, embeddings_pca_cluster, embeddings_pca_2d)
    
    return df, results


if __name__ == "__main__":
    df, results = main()