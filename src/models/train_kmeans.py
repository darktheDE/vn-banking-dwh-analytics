"""Task C-06 / C-07 / C-08: PCA + K-Means clustering of 46 commercial banks.

Determines optimal PCA components (>=80% explained variance) and optimal k
via Elbow + Silhouette. Logs Silhouette Score and Davies-Bouldin Index.
Writes cluster assignments to BigQuery.

See docs/ml-spec.md Section 2 for full specification.
"""

import os

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/batch environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score, silhouette_score

from src.models.feature_engineering_bank import (
    CAMELS_FEATURES,
    build_bank_features,
)
from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
PCA_VARIANCE_THRESHOLD = 0.80   # Retain components explaining >= 80% variance
K_RANGE = range(2, 11)          # Candidate cluster counts for Elbow/Silhouette
RANDOM_STATE = 42
FIGURES_DIR = os.path.join("reports", "figures")


def determine_pca_components(
    scaled_data: np.ndarray,
) -> tuple[PCA, np.ndarray]:
    """Apply PCA and determine the optimal number of components.

    Retains enough components to explain at least PCA_VARIANCE_THRESHOLD
    of the total variance (docs/ml-spec.md Section 2.3).

    Args:
        scaled_data: 2D array of standardized features.

    Returns:
        Tuple of (fitted PCA object, transformed data).
    """
    # First, fit full PCA to inspect cumulative variance
    full_pca = PCA(random_state=RANDOM_STATE)
    full_pca.fit(scaled_data)
    cumulative_variance = np.cumsum(full_pca.explained_variance_ratio_)

    # Find number of components for >= threshold
    n_components = int(
        np.argmax(cumulative_variance >= PCA_VARIANCE_THRESHOLD) + 1
    )
    logger.info(
        "PCA: %d components explain %.2f%% of variance (threshold: %.0f%%).",
        n_components,
        cumulative_variance[n_components - 1] * 100,
        PCA_VARIANCE_THRESHOLD * 100,
    )

    # Plot cumulative explained variance
    os.makedirs(FIGURES_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        range(1, len(cumulative_variance) + 1),
        cumulative_variance,
        marker="o",
        linewidth=2,
    )
    ax.axhline(
        y=PCA_VARIANCE_THRESHOLD,
        color="r",
        linestyle="--",
        label=f"{PCA_VARIANCE_THRESHOLD * 100:.0f}% threshold",
    )
    ax.axvline(
        x=n_components,
        color="g",
        linestyle="--",
        label=f"Selected: {n_components} components",
    )
    ax.set_xlabel("Number of Components")
    ax.set_ylabel("Cumulative Explained Variance")
    ax.set_title("PCA — Cumulative Explained Variance")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    pca_plot_path = os.path.join(FIGURES_DIR, "pca_explained_variance.png")
    fig.savefig(pca_plot_path, dpi=150)
    plt.close(fig)
    logger.info("PCA variance plot saved to %s.", pca_plot_path)

    # Fit final PCA with optimal number of components
    pca = PCA(n_components=n_components, random_state=RANDOM_STATE)
    transformed = pca.fit_transform(scaled_data)

    return pca, transformed


def find_optimal_k(
    data: np.ndarray,
) -> int:
    """Determine optimal k using Elbow Method and Silhouette Analysis.

    Both methods are required per docs/ml-spec.md Section 2.3.

    Args:
        data: PCA-transformed data array.

    Returns:
        The selected optimal number of clusters.
    """
    inertias = []
    silhouette_scores = []

    for k in K_RANGE:
        kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = kmeans.fit_predict(data)
        inertias.append(kmeans.inertia_)
        sil = silhouette_score(data, labels)
        silhouette_scores.append(sil)
        logger.info("K=%d — Inertia: %.2f, Silhouette: %.4f", k, kmeans.inertia_, sil)

    # ── Elbow Plot ──
    os.makedirs(FIGURES_DIR, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(list(K_RANGE), inertias, marker="o", linewidth=2)
    axes[0].set_xlabel("Number of Clusters (k)")
    axes[0].set_ylabel("Inertia (Within-Cluster Sum of Squares)")
    axes[0].set_title("Elbow Method")
    axes[0].grid(True, alpha=0.3)

    # ── Silhouette Plot ──
    axes[1].plot(list(K_RANGE), silhouette_scores, marker="s", linewidth=2, color="orange")
    axes[1].set_xlabel("Number of Clusters (k)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].set_title("Silhouette Analysis")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    elbow_path = os.path.join(FIGURES_DIR, "kmeans_elbow_silhouette.png")
    fig.savefig(elbow_path, dpi=150)
    plt.close(fig)
    logger.info("Elbow and Silhouette plots saved to %s.", elbow_path)

    # Select k with the highest silhouette score
    best_k = list(K_RANGE)[int(np.argmax(silhouette_scores))]
    logger.info(
        "Optimal k selected: %d (Silhouette Score: %.4f).",
        best_k,
        max(silhouette_scores),
    )

    return best_k


def train_kmeans_clustering() -> dict:
    """Execute the full K-Means + PCA clustering pipeline.

    Steps:
      1. Load scaled bank features via C-02.
      2. Apply PCA for dimensionality reduction.
      3. Determine optimal k via Elbow and Silhouette.
      4. Train final K-Means model.
      5. Evaluate with Silhouette Score and Davies-Bouldin Index.
      6. Write cluster assignments to BigQuery.

    Returns:
        Dictionary with evaluation metrics and cluster statistics.
    """
    config = load_config()

    # ── Step 1: Load scaled bank features ──
    # Use the latest year per bank for clustering (cross-sectional snapshot)
    df, scaler = build_bank_features(scale=True)

    # Get the latest year per bank for clustering
    df_latest = (
        df.sort_values("date_key")
        .groupby("bank_key")
        .last()
        .reset_index()
    )
    logger.info(
        "Using %d banks (latest year per bank) for clustering.",
        len(df_latest),
    )

    # Extract scaled feature matrix
    available_features = [c for c in CAMELS_FEATURES if c in df_latest.columns]
    feature_matrix = df_latest[available_features].values

    # ── Step 2: PCA ──
    pca, pca_data = determine_pca_components(feature_matrix)

    # ── Step 3: Optimal k ──
    optimal_k = find_optimal_k(pca_data)

    # ── Step 4: Train final K-Means ──
    final_kmeans = KMeans(
        n_clusters=optimal_k, random_state=RANDOM_STATE, n_init=10
    )
    cluster_labels = final_kmeans.fit_predict(pca_data)

    # ── Step 5: Evaluation metrics ──
    sil_score = silhouette_score(pca_data, cluster_labels)
    db_index = davies_bouldin_score(pca_data, cluster_labels)

    logger.info("Final K-Means (k=%d) — Silhouette Score: %.4f", optimal_k, sil_score)
    logger.info("Final K-Means (k=%d) — Davies-Bouldin Index: %.4f", optimal_k, db_index)

    # Add cluster labels to the DataFrame
    df_latest = df_latest.copy()
    df_latest["cluster_id"] = cluster_labels

    # Log cluster distribution
    cluster_counts = df_latest["cluster_id"].value_counts().sort_index()
    for cluster_id, count in cluster_counts.items():
        banks_in_cluster = df_latest.loc[
            df_latest["cluster_id"] == cluster_id, "bank_code"
        ].tolist()
        logger.info(
            "Cluster %d: %d banks — %s",
            cluster_id,
            count,
            banks_in_cluster,
        )

    # ── Plot cluster scatter (first 2 PCA components) ──
    if pca_data.shape[1] >= 2:
        fig, ax = plt.subplots(figsize=(10, 7))
        scatter = ax.scatter(
            pca_data[:, 0],
            pca_data[:, 1],
            c=cluster_labels,
            cmap="viridis",
            s=80,
            edgecolors="k",
            alpha=0.7,
        )
        # Annotate each point with bank_code
        for i, code in enumerate(df_latest["bank_code"]):
            ax.annotate(
                code,
                (pca_data[i, 0], pca_data[i, 1]),
                fontsize=7,
                ha="center",
                va="bottom",
            )
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title(f"K-Means Clustering (k={optimal_k}) on PCA Components")
        fig.colorbar(scatter, label="Cluster ID")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        scatter_path = os.path.join(FIGURES_DIR, "kmeans_cluster_scatter.png")
        fig.savefig(scatter_path, dpi=150)
        plt.close(fig)
        logger.info("Cluster scatter plot saved to %s.", scatter_path)

    # ── Step 6: Save model artifacts ──
    os.makedirs(config.model_artifact_path, exist_ok=True)
    import pickle
    with open(os.path.join(config.model_artifact_path, "kmeans_model.pkl"), "wb") as f:
        pickle.dump(final_kmeans, f)
    with open(os.path.join(config.model_artifact_path, "pca_model.pkl"), "wb") as f:
        pickle.dump(pca, f)
    if scaler is not None:
        with open(os.path.join(config.model_artifact_path, "scaler_bank.pkl"), "wb") as f:
            pickle.dump(scaler, f)
    logger.info("Saved K-Means, PCA, and Scaler model artifacts.")

    # ── Step 7: Write to BigQuery ──
    _write_clusters_to_bigquery(df_latest, config)

    return {
        "optimal_k": optimal_k,
        "silhouette_score": sil_score,
        "davies_bouldin_index": db_index,
        "n_pca_components": pca.n_components_,
        "cluster_distribution": cluster_counts.to_dict(),
    }


def _write_clusters_to_bigquery(
    df: pd.DataFrame,
    config,
) -> None:
    """Write cluster assignment results to BigQuery.

    Args:
        df: DataFrame with bank identification and cluster_id column.
        config: Application configuration.
    """
    output_df = df[["bank_key", "bank_code", "bank_name", "bank_type", "cluster_id"]].copy()
    output_df["model_name"] = "KMeans_PCA"

    client = get_bigquery_client()
    table_id = get_full_table_id("bank_cluster_assignments")

    from google.cloud import bigquery as bq

    job_config = bq.LoadJobConfig(
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_dataframe(
        output_df, table_id, job_config=job_config
    )
    job.result()

    logger.info(
        "Successfully wrote %d cluster assignments to %s.",
        len(output_df),
        table_id,
    )


if __name__ == "__main__":
    results = train_kmeans_clustering()
    logger.info("K-Means clustering pipeline complete. Results: %s", results)
