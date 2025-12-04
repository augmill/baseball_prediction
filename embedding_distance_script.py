"""
Embedding Distance Analysis
============================
This script analyzes whether at-bats with the same outcome (event) are
closer together in embedding space than random pairs.

Key Questions:
1. Are same-event pairs closer than different-event pairs?
2. Which events (if any) have the tightest clusters?
3. Is there ANY outcome signal in the embeddings?

Requirements:
    pip install pandas numpy scikit-learn matplotlib seaborn scipy
"""

import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist, pdist, squareform
from scipy import stats
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================
RANDOM_STATE = 42
N_SAMPLE_PAIRS = 10000  # Number of pairs to sample for comparison
np.random.seed(RANDOM_STATE)


def load_data():
    """Load the saved embeddings and results from previous analysis"""
    print("=" * 60)
    print("Loading Data from Previous Analysis")
    print("=" * 60)
    
    # Load the saved data
    try:
        df = pd.read_csv('baseball_clustering_results.csv')
        embeddings_pca = np.load('embeddings_pca_cluster.npy')
        embeddings_2d = np.load('embeddings_pca_2d.npy')
        print(f"✓ Loaded {len(df)} samples")
        print(f"✓ Embeddings shape: {embeddings_pca.shape}")
        return df, embeddings_pca, embeddings_2d
    except FileNotFoundError:
        print("ERROR: Could not find saved files from previous analysis.")
        print("Please run the clustering script first.")
        raise


def compute_pairwise_distances_sampled(embeddings, df, n_pairs=10000):
    """
    Compute distances between sampled pairs of same-event and different-event at-bats
    """
    print("\n" + "=" * 60)
    print("STEP 1: Computing Pairwise Distances")
    print("=" * 60)
    
    events = df['events'].values
    unique_events = np.unique(events)
    n_samples = len(df)
    
    same_event_distances = []
    diff_event_distances = []
    
    print(f"\nSampling {n_pairs} pairs each for same-event and different-event comparisons...")
    
    # Sample same-event pairs
    same_count = 0
    attempts = 0
    max_attempts = n_pairs * 10
    
    while same_count < n_pairs and attempts < max_attempts:
        i, j = np.random.randint(0, n_samples, 2)
        if i != j and events[i] == events[j]:
            dist = np.linalg.norm(embeddings[i] - embeddings[j])
            same_event_distances.append({
                'distance': dist,
                'event': events[i],
                'type': 'Same Event'
            })
            same_count += 1
        attempts += 1
    
    print(f"  ✓ Sampled {len(same_event_distances)} same-event pairs")
    
    # Sample different-event pairs
    diff_count = 0
    attempts = 0
    
    while diff_count < n_pairs and attempts < max_attempts:
        i, j = np.random.randint(0, n_samples, 2)
        if i != j and events[i] != events[j]:
            dist = np.linalg.norm(embeddings[i] - embeddings[j])
            diff_event_distances.append({
                'distance': dist,
                'event_1': events[i],
                'event_2': events[j],
                'type': 'Different Event'
            })
            diff_count += 1
        attempts += 1
    
    print(f"  ✓ Sampled {len(diff_event_distances)} different-event pairs")
    
    return same_event_distances, diff_event_distances


def statistical_comparison(same_event_distances, diff_event_distances):
    """
    Perform statistical tests comparing same-event vs different-event distances
    """
    print("\n" + "=" * 60)
    print("STEP 2: Statistical Comparison")
    print("=" * 60)
    
    same_dists = [d['distance'] for d in same_event_distances]
    diff_dists = [d['distance'] for d in diff_event_distances]
    
    # Basic statistics
    print("\n--- Distance Statistics ---")
    print(f"\nSame-Event Pairs (n={len(same_dists)}):")
    print(f"  Mean distance:   {np.mean(same_dists):.4f}")
    print(f"  Median distance: {np.median(same_dists):.4f}")
    print(f"  Std deviation:   {np.std(same_dists):.4f}")
    print(f"  Min:             {np.min(same_dists):.4f}")
    print(f"  Max:             {np.max(same_dists):.4f}")
    
    print(f"\nDifferent-Event Pairs (n={len(diff_dists)}):")
    print(f"  Mean distance:   {np.mean(diff_dists):.4f}")
    print(f"  Median distance: {np.median(diff_dists):.4f}")
    print(f"  Std deviation:   {np.std(diff_dists):.4f}")
    print(f"  Min:             {np.min(diff_dists):.4f}")
    print(f"  Max:             {np.max(diff_dists):.4f}")
    
    # Statistical tests
    print("\n--- Statistical Tests ---")
    
    # T-test
    t_stat, t_pvalue = stats.ttest_ind(same_dists, diff_dists)
    print(f"\nIndependent t-test:")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value:     {t_pvalue:.4e}")
    
    # Mann-Whitney U test (non-parametric)
    u_stat, u_pvalue = stats.mannwhitneyu(same_dists, diff_dists, alternative='two-sided')
    print(f"\nMann-Whitney U test:")
    print(f"  U-statistic: {u_stat:.4f}")
    print(f"  p-value:     {u_pvalue:.4e}")
    
    # Effect size (Cohen's d)
    pooled_std = np.sqrt((np.std(same_dists)**2 + np.std(diff_dists)**2) / 2)
    cohens_d = (np.mean(same_dists) - np.mean(diff_dists)) / pooled_std
    print(f"\nEffect Size (Cohen's d): {cohens_d:.4f}")
    
    # Interpretation
    print("\n--- Interpretation ---")
    
    mean_diff = np.mean(same_dists) - np.mean(diff_dists)
    mean_diff_pct = (mean_diff / np.mean(diff_dists)) * 100
    
    if t_pvalue < 0.05:
        if mean_diff < 0:
            print(f"✓ SIGNIFICANT: Same-event pairs ARE closer together")
            print(f"  Same-event pairs are {abs(mean_diff_pct):.2f}% closer on average")
        else:
            print(f"✗ SIGNIFICANT but OPPOSITE: Same-event pairs are FARTHER apart!")
            print(f"  Same-event pairs are {abs(mean_diff_pct):.2f}% farther on average")
    else:
        print(f"✗ NOT SIGNIFICANT: No meaningful difference between same-event and different-event distances")
    
    if abs(cohens_d) < 0.2:
        print(f"  Effect size is NEGLIGIBLE (Cohen's d = {cohens_d:.4f})")
    elif abs(cohens_d) < 0.5:
        print(f"  Effect size is SMALL (Cohen's d = {cohens_d:.4f})")
    elif abs(cohens_d) < 0.8:
        print(f"  Effect size is MEDIUM (Cohen's d = {cohens_d:.4f})")
    else:
        print(f"  Effect size is LARGE (Cohen's d = {cohens_d:.4f})")
    
    results = {
        'same_mean': np.mean(same_dists),
        'diff_mean': np.mean(diff_dists),
        'same_median': np.median(same_dists),
        'diff_median': np.median(diff_dists),
        't_stat': t_stat,
        't_pvalue': t_pvalue,
        'u_stat': u_stat,
        'u_pvalue': u_pvalue,
        'cohens_d': cohens_d,
        'mean_diff_pct': mean_diff_pct
    }
    
    return results, same_dists, diff_dists


def per_event_analysis(same_event_distances, embeddings, df):
    """
    Analyze which events have the tightest/loosest clusters
    """
    print("\n" + "=" * 60)
    print("STEP 3: Per-Event Distance Analysis")
    print("=" * 60)
    
    # Group distances by event
    event_distances = defaultdict(list)
    for d in same_event_distances:
        event_distances[d['event']].append(d['distance'])
    
    # Calculate statistics per event
    event_stats = []
    for event, distances in event_distances.items():
        if len(distances) >= 10:  # Need enough samples
            event_stats.append({
                'event': event,
                'n_pairs': len(distances),
                'n_samples': (df['events'] == event).sum(),
                'mean_dist': np.mean(distances),
                'median_dist': np.median(distances),
                'std_dist': np.std(distances),
                'min_dist': np.min(distances),
                'max_dist': np.max(distances)
            })
    
    event_stats_df = pd.DataFrame(event_stats).sort_values('mean_dist')
    
    print("\nWithin-Event Distance Statistics (sorted by mean distance):")
    print("=" * 80)
    print(f"{'Event':<10} {'N Samples':<12} {'N Pairs':<10} {'Mean Dist':<12} {'Median':<12} {'Std':<10}")
    print("-" * 80)
    
    for _, row in event_stats_df.iterrows():
        print(f"Event_{int(row['event']):<4} {int(row['n_samples']):<12} {int(row['n_pairs']):<10} "
              f"{row['mean_dist']:<12.4f} {row['median_dist']:<12.4f} {row['std_dist']:<10.4f}")
    
    print("\n--- Interpretation ---")
    tightest = event_stats_df.iloc[0]
    loosest = event_stats_df.iloc[-1]
    
    print(f"\nTightest cluster: Event_{int(tightest['event'])} (mean dist = {tightest['mean_dist']:.4f})")
    print(f"Loosest cluster:  Event_{int(loosest['event'])} (mean dist = {loosest['mean_dist']:.4f})")
    
    # Check if there's meaningful variation
    mean_range = loosest['mean_dist'] - tightest['mean_dist']
    overall_mean = event_stats_df['mean_dist'].mean()
    variation_pct = (mean_range / overall_mean) * 100
    
    print(f"\nVariation across events: {variation_pct:.1f}%")
    if variation_pct < 10:
        print("→ Very little variation - all events have similar spread")
    elif variation_pct < 25:
        print("→ Moderate variation - some events slightly tighter than others")
    else:
        print("→ Substantial variation - some events cluster more tightly")
    
    return event_stats_df


def compute_inter_event_distances(embeddings, df, n_samples_per_event=100):
    """
    Compute mean distances between different event types
    """
    print("\n" + "=" * 60)
    print("STEP 4: Inter-Event Distance Matrix")
    print("=" * 60)
    
    events = df['events'].values
    unique_events = sorted(df['events'].unique())
    n_events = len(unique_events)
    
    # Sample embeddings for each event
    event_embeddings = {}
    for event in unique_events:
        mask = events == event
        indices = np.where(mask)[0]
        if len(indices) > n_samples_per_event:
            indices = np.random.choice(indices, n_samples_per_event, replace=False)
        event_embeddings[event] = embeddings[indices]
    
    # Compute mean distance between each pair of events
    distance_matrix = np.zeros((n_events, n_events))
    
    print("\nComputing inter-event distances...")
    for i, event_i in enumerate(unique_events):
        for j, event_j in enumerate(unique_events):
            if i <= j:
                # Compute pairwise distances between samples of two events
                dists = cdist(event_embeddings[event_i], event_embeddings[event_j])
                mean_dist = np.mean(dists)
                distance_matrix[i, j] = mean_dist
                distance_matrix[j, i] = mean_dist
    
    # Create DataFrame for visualization
    dist_df = pd.DataFrame(
        distance_matrix,
        index=[f'Event_{e}' for e in unique_events],
        columns=[f'Event_{e}' for e in unique_events]
    )
    
    print("\nInter-Event Distance Matrix (mean distances):")
    print(dist_df.round(3).to_string())
    
    # Find most similar and most different event pairs
    print("\n--- Most Similar Event Pairs ---")
    # Get upper triangle indices (excluding diagonal)
    triu_indices = np.triu_indices(n_events, k=1)
    distances_flat = distance_matrix[triu_indices]
    event_pairs = [(unique_events[i], unique_events[j]) for i, j in zip(*triu_indices)]
    
    sorted_indices = np.argsort(distances_flat)
    
    print("\nClosest event pairs:")
    for idx in sorted_indices[:5]:
        e1, e2 = event_pairs[idx]
        dist = distances_flat[idx]
        print(f"  Event_{e1} ↔ Event_{e2}: {dist:.4f}")
    
    print("\nMost distant event pairs:")
    for idx in sorted_indices[-5:]:
        e1, e2 = event_pairs[idx]
        dist = distances_flat[idx]
        print(f"  Event_{e1} ↔ Event_{e2}: {dist:.4f}")
    
    return dist_df, unique_events


def create_visualizations(same_dists, diff_dists, event_stats_df, dist_matrix_df, results):
    """
    Create visualizations for distance analysis
    """
    print("\n" + "=" * 60)
    print("STEP 5: Creating Visualizations")
    print("=" * 60)
    
    # -------------------------------------------------------------------------
    # 1. Distribution comparison: Same vs Different event distances
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Histogram
    axes[0].hist(same_dists, bins=50, alpha=0.6, label='Same Event', color='blue', density=True)
    axes[0].hist(diff_dists, bins=50, alpha=0.6, label='Different Event', color='red', density=True)
    axes[0].axvline(np.mean(same_dists), color='blue', linestyle='--', linewidth=2, label=f'Same Mean: {np.mean(same_dists):.3f}')
    axes[0].axvline(np.mean(diff_dists), color='red', linestyle='--', linewidth=2, label=f'Diff Mean: {np.mean(diff_dists):.3f}')
    axes[0].set_xlabel('Euclidean Distance', fontsize=12)
    axes[0].set_ylabel('Density', fontsize=12)
    axes[0].set_title('Distance Distribution: Same vs Different Event Pairs', fontsize=14)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Box plot
    data_for_box = pd.DataFrame({
        'Distance': same_dists + diff_dists,
        'Type': ['Same Event'] * len(same_dists) + ['Different Event'] * len(diff_dists)
    })
    sns.boxplot(data=data_for_box, x='Type', y='Distance', ax=axes[1], palette=['blue', 'red'])
    axes[1].set_title('Distance Comparison: Same vs Different Event Pairs', fontsize=14)
    axes[1].set_ylabel('Euclidean Distance', fontsize=12)
    axes[1].grid(True, alpha=0.3)
    
    # Add statistical annotation
    sig_text = f"Cohen's d = {results['cohens_d']:.4f}\np-value = {results['t_pvalue']:.2e}"
    axes[1].text(0.5, 0.95, sig_text, transform=axes[1].transAxes, 
                fontsize=11, verticalalignment='top', horizontalalignment='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('12_distance_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 12_distance_comparison.png")
    
    # -------------------------------------------------------------------------
    # 2. Per-event distance analysis
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Bar chart of mean distances per event
    event_stats_sorted = event_stats_df.sort_values('mean_dist')
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(event_stats_sorted)))
    
    bars = axes[0].bar(range(len(event_stats_sorted)), event_stats_sorted['mean_dist'], 
                       color=colors, edgecolor='black')
    axes[0].set_xticks(range(len(event_stats_sorted)))
    axes[0].set_xticklabels([f"Event_{int(e)}" for e in event_stats_sorted['event']], rotation=45, ha='right')
    axes[0].set_xlabel('Event Type', fontsize=12)
    axes[0].set_ylabel('Mean Within-Event Distance', fontsize=12)
    axes[0].set_title('Cluster Tightness by Event Type\n(Lower = Tighter Cluster)', fontsize=14)
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # Add sample count annotations
    for i, (_, row) in enumerate(event_stats_sorted.iterrows()):
        axes[0].text(i, row['mean_dist'] + 0.1, f"n={int(row['n_samples'])}", 
                    ha='center', fontsize=8, rotation=90)
    
    # Scatter: mean distance vs sample count
    axes[1].scatter(event_stats_df['n_samples'], event_stats_df['mean_dist'], 
                   s=100, c=event_stats_df['mean_dist'], cmap='RdYlGn_r', 
                   edgecolors='black', linewidths=1)
    
    for _, row in event_stats_df.iterrows():
        axes[1].annotate(f"E{int(row['event'])}", 
                        (row['n_samples'], row['mean_dist']),
                        textcoords="offset points", xytext=(5, 5), fontsize=9)
    
    axes[1].set_xlabel('Number of Samples', fontsize=12)
    axes[1].set_ylabel('Mean Within-Event Distance', fontsize=12)
    axes[1].set_title('Cluster Tightness vs Sample Size', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('13_per_event_distances.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 13_per_event_distances.png")
    
    # -------------------------------------------------------------------------
    # 3. Inter-event distance heatmap
    # -------------------------------------------------------------------------
    plt.figure(figsize=(12, 10))
    
    # Mask diagonal for clearer visualization
    mask = np.eye(len(dist_matrix_df), dtype=bool)
    
    sns.heatmap(dist_matrix_df, annot=True, fmt='.2f', cmap='RdYlGn_r',
                mask=mask, linewidths=0.5, cbar_kws={'label': 'Mean Distance'},
                vmin=dist_matrix_df.values[~mask].min(),
                vmax=dist_matrix_df.values[~mask].max())
    plt.title('Inter-Event Distance Matrix\n(Mean distance between event types)', fontsize=14)
    plt.tight_layout()
    plt.savefig('14_inter_event_distances.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 14_inter_event_distances.png")
    
    # -------------------------------------------------------------------------
    # 4. Summary visualization
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create summary text
    summary_text = f"""
    EMBEDDING DISTANCE ANALYSIS SUMMARY
    {'='*50}
    
    QUESTION: Are same-outcome at-bats closer in embedding space?
    
    RESULTS:
    • Same-event pair mean distance:      {results['same_mean']:.4f}
    • Different-event pair mean distance: {results['diff_mean']:.4f}
    • Difference:                         {results['mean_diff_pct']:.2f}%
    
    STATISTICAL SIGNIFICANCE:
    • t-test p-value:  {results['t_pvalue']:.2e}
    • Effect size (d): {results['cohens_d']:.4f}
    
    INTERPRETATION:
    {'='*50}
    """
    
    if abs(results['cohens_d']) < 0.2:
        conclusion = """
    ╔════════════════════════════════════════════════════════╗
    ║  NEGLIGIBLE EFFECT SIZE                                ║
    ║                                                        ║
    ║  Same-outcome at-bats are NOT meaningfully closer      ║
    ║  together than different-outcome at-bats.              ║
    ║                                                        ║
    ║  The embeddings contain NO useful outcome signal.      ║
    ║  They capture CONTEXT (who's playing), not OUTCOMES.   ║
    ╚════════════════════════════════════════════════════════╝
        """
    elif abs(results['cohens_d']) < 0.5:
        conclusion = """
    ╔════════════════════════════════════════════════════════╗
    ║  SMALL EFFECT SIZE                                     ║
    ║                                                        ║
    ║  There is a small but detectable tendency for          ║
    ║  same-outcome at-bats to cluster slightly closer.      ║
    ║                                                        ║
    ║  However, the effect is too weak for prediction.       ║
    ╚════════════════════════════════════════════════════════╝
        """
    else:
        conclusion = """
    ╔════════════════════════════════════════════════════════╗
    ║  MEANINGFUL EFFECT SIZE                                ║
    ║                                                        ║
    ║  Same-outcome at-bats DO cluster closer together!      ║
    ║  The embeddings contain some outcome-predictive        ║
    ║  information that could potentially be exploited.      ║
    ╚════════════════════════════════════════════════════════╝
        """
    
    summary_text += conclusion
    
    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray'))
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('15_distance_analysis_summary.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✓ Saved: 15_distance_analysis_summary.png")


def generate_report(results, event_stats_df):
    """Generate final report"""
    print("\n" + "=" * 60)
    print("FINAL REPORT: Embedding Distance Analysis")
    print("=" * 60)
    
    print(f"""
┌────────────────────────────────────────────────────────────┐
│  KEY FINDING                                               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Same-event mean distance:      {results['same_mean']:.4f}                   │
│  Different-event mean distance: {results['diff_mean']:.4f}                   │
│  Difference:                    {results['mean_diff_pct']:+.2f}%                   │
│                                                            │
│  Cohen's d effect size:         {results['cohens_d']:.4f}                    │
│  Statistical significance:      p = {results['t_pvalue']:.2e}            │
│                                                            │
└────────────────────────────────────────────────────────────┘
    """)
    
    if abs(results['cohens_d']) < 0.2:
        print("""
CONCLUSION:
===========
The embeddings DO NOT contain meaningful outcome information.

At-bats with the same outcome are NOT closer together in embedding
space than at-bats with different outcomes. The tiny difference 
observed ({:.2f}%) is negligible and has no practical significance.

This confirms that the sentence embeddings capture CONTEXT 
(players, game situation, matchups) rather than OUTCOMES.

IMPLICATION: You cannot use embedding similarity to predict 
baseball outcomes. The same context can produce any outcome.
        """.format(abs(results['mean_diff_pct'])))
    else:
        print(f"""
CONCLUSION:
===========
There IS a detectable ({abs(results['mean_diff_pct']):.2f}%) difference in distances.
Same-outcome at-bats are {'closer' if results['mean_diff_pct'] < 0 else 'farther'} together.

Effect size: {results['cohens_d']:.4f} ({'negligible' if abs(results['cohens_d']) < 0.2 else 'small' if abs(results['cohens_d']) < 0.5 else 'medium' if abs(results['cohens_d']) < 0.8 else 'large'})
        """)
    
    print("\nSAVED FILES:")
    print("  12_distance_comparison.png      - Same vs different event distributions")
    print("  13_per_event_distances.png      - Per-event cluster tightness")
    print("  14_inter_event_distances.png    - Distance matrix between events")
    print("  15_distance_analysis_summary.png - Visual summary")


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "=" * 60)
    print("EMBEDDING DISTANCE ANALYSIS")
    print("=" * 60)
    print("\nQuestion: Are at-bats with the same outcome closer together")
    print("          in embedding space than random pairs?")
    
    # Load data
    df, embeddings_pca, embeddings_2d = load_data()
    
    # Compute pairwise distances
    same_event_distances, diff_event_distances = compute_pairwise_distances_sampled(
        embeddings_pca, df, n_pairs=N_SAMPLE_PAIRS
    )
    
    # Statistical comparison
    results, same_dists, diff_dists = statistical_comparison(
        same_event_distances, diff_event_distances
    )
    
    # Per-event analysis
    event_stats_df = per_event_analysis(same_event_distances, embeddings_pca, df)
    
    # Inter-event distance matrix
    dist_matrix_df, unique_events = compute_inter_event_distances(embeddings_pca, df)
    
    # Visualizations
    create_visualizations(same_dists, diff_dists, event_stats_df, dist_matrix_df, results)
    
    # Final report
    generate_report(results, event_stats_df)
    
    return results, event_stats_df, dist_matrix_df


if __name__ == "__main__":
    results, event_stats_df, dist_matrix_df = main()