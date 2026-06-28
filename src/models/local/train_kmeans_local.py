"""
K-Means Local — Phân cụm 45 ngân hàng thương mại Việt Nam.

Đọc dữ liệu từ data/ML_data/banks_camels_46.csv (667 quan sát, 45 ngân hàng).
Sử dụng StandardScaler -> PCA (>= 80% variance) -> K-Means.
Đánh giá bằng Silhouette Score và Davies-Bouldin Index.
Xuất kết quả phân cụm ra data/ML_data/kmeans_clusters_local.csv.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import davies_bouldin_score, silhouette_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from src.utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
ML_DATA_DIR = os.path.join(BASE_DIR, "data", "data_ml")
FIGURES_DIR = os.path.join(ML_DATA_DIR, "figures")

# Config
PCA_VARIANCE_THRESHOLD = 0.80
K_RANGE = range(2, 11)
RANDOM_STATE = 42

CAMELS_FEATURES = [
    "npl_ratio", "llp_ratio", "roa", "roe", "nim", "cir",
    "eta", "etd", "lta", "ltd", "gta",
]


def train_kmeans():
    """Pipeline chính: Load data -> PCA -> Tìm k tối ưu -> K-Means -> Export."""
    data_path = os.path.join(ML_DATA_DIR, "banks_camels_46.csv")
    if not os.path.exists(data_path):
        logger.error("Data not found at %s. Run data_loader.py first.", data_path)
        return None

    df = pd.read_csv(data_path)
    logger.info("Loaded %d rows, %d banks.", len(df), df["bank_key"].nunique())

    # Lấy dữ liệu năm mới nhất cho mỗi ngân hàng (cross-sectional snapshot)
    df_latest = df.sort_values("date_key").groupby("bank_key").last().reset_index()
    logger.info("Using %d banks (latest year per bank) for clustering.", len(df_latest))

    # Lọc các cột CAMELS có sẵn
    available_features = [c for c in CAMELS_FEATURES if c in df_latest.columns]
    logger.info("Using %d CAMELS features: %s", len(available_features), available_features)

    feature_matrix = df_latest[available_features].fillna(0).values

    # StandardScaler (bắt buộc theo ml-spec.md Section 2.2)
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(feature_matrix)

    # --- PCA ---
    full_pca = PCA(random_state=RANDOM_STATE)
    full_pca.fit(scaled_data)
    cumulative_var = np.cumsum(full_pca.explained_variance_ratio_)
    n_components = int(np.argmax(cumulative_var >= PCA_VARIANCE_THRESHOLD) + 1)
    logger.info("PCA: %d components explain %.2f%% of variance (threshold: %.0f%%).",
                n_components, cumulative_var[n_components - 1] * 100, PCA_VARIANCE_THRESHOLD * 100)

    pca = PCA(n_components=n_components, random_state=RANDOM_STATE)
    pca_data = pca.fit_transform(scaled_data)

    # Plot PCA Explained Variance
    os.makedirs(FIGURES_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(cumulative_var) + 1), cumulative_var, marker="o", linewidth=2)
    ax.axhline(y=PCA_VARIANCE_THRESHOLD, color="r", linestyle="--",
               label=f"{PCA_VARIANCE_THRESHOLD*100:.0f}% threshold")
    ax.axvline(x=n_components, color="g", linestyle="--",
               label=f"Selected: {n_components} components")
    ax.set_xlabel("Number of Components")
    ax.set_ylabel("Cumulative Explained Variance")
    ax.set_title("PCA — Cumulative Explained Variance")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "pca_explained_variance.png"), dpi=150)
    plt.close(fig)

    # --- Tìm k tối ưu (Elbow + Silhouette) ---
    inertias, sil_scores = [], []
    for k in K_RANGE:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(pca_data)
        inertias.append(km.inertia_)
        sil = silhouette_score(pca_data, labels)
        sil_scores.append(sil)
        logger.info("K=%d — Inertia: %.2f, Silhouette: %.4f", k, km.inertia_, sil)

    # Plot Elbow + Silhouette
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(list(K_RANGE), inertias, marker="o", linewidth=2)
    axes[0].set_xlabel("Number of Clusters (k)")
    axes[0].set_ylabel("Inertia")
    axes[0].set_title("Elbow Method")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(list(K_RANGE), sil_scores, marker="s", linewidth=2, color="orange")
    axes[1].set_xlabel("Number of Clusters (k)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].set_title("Silhouette Analysis")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "kmeans_elbow_silhouette.png"), dpi=150)
    plt.close(fig)

    # Chọn k có Silhouette Score cao nhất
    optimal_k = list(K_RANGE)[int(np.argmax(sil_scores))]
    logger.info("Optimal k selected: %d (Silhouette Score: %.4f)", optimal_k, max(sil_scores))

    # --- Train K-Means chính thức ---
    final_km = KMeans(n_clusters=optimal_k, random_state=RANDOM_STATE, n_init=10)
    cluster_labels = final_km.fit_predict(pca_data)

    sil_final = silhouette_score(pca_data, cluster_labels)
    db_index = davies_bouldin_score(pca_data, cluster_labels)
    logger.info("Final K-Means (k=%d) — Silhouette: %.4f, Davies-Bouldin: %.4f",
                optimal_k, sil_final, db_index)

    df_latest["cluster_id"] = cluster_labels

    # Log cluster distribution
    for cid in sorted(df_latest["cluster_id"].unique()):
        banks = df_latest.loc[df_latest["cluster_id"] == cid]
        if "bank_code" in banks.columns:
            bank_list = banks["bank_code"].tolist()
        else:
            bank_list = banks["bank_key"].tolist()
        logger.info("Cluster %d: %d banks — %s", cid, len(banks), bank_list)

    # Plot cluster scatter (PC1 vs PC2)
    if pca_data.shape[1] >= 2:
        fig, ax = plt.subplots(figsize=(10, 7))
        scatter = ax.scatter(pca_data[:, 0], pca_data[:, 1], c=cluster_labels,
                             cmap="viridis", s=80, edgecolors="k", alpha=0.7)
        if "bank_code" in df_latest.columns:
            for i, code in enumerate(df_latest["bank_code"]):
                ax.annotate(str(code), (pca_data[i, 0], pca_data[i, 1]),
                            fontsize=6, ha="center", va="bottom")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title(f"K-Means Clustering (k={optimal_k}) on PCA Components")
        fig.colorbar(scatter, label="Cluster ID")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGURES_DIR, "kmeans_cluster_scatter.png"), dpi=150)
        plt.close(fig)

    # --- Export ---
    output_cols = ["bank_key", "date_key", "year", "cluster_id"]
    if "bank_code" in df_latest.columns:
        output_cols.insert(1, "bank_code")
    out_path = os.path.join(ML_DATA_DIR, "kmeans_clusters_local.csv")
    df_latest[output_cols].to_csv(out_path, index=False)
    logger.info("Saved cluster assignments to %s", out_path)

    return {
        "optimal_k": optimal_k,
        "silhouette_score": sil_final,
        "davies_bouldin_index": db_index,
        "n_pca_components": n_components,
        "n_banks": len(df_latest),
    }


if __name__ == "__main__":
    results = train_kmeans()
    if results:
        logger.info("K-Means pipeline complete. k=%d, Silhouette=%.4f, DB=%.4f",
                     results["optimal_k"], results["silhouette_score"],
                     results["davies_bouldin_index"])
