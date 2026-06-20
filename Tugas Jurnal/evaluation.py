"""
=============================================================
TUGAS JURNAL - PERFORMANCE EVALUATION SCRIPT
=============================================================
Mengevaluasi kinerja penemuan (retrieval) siswa berprestasi
antara Baseline (TF-IDF + BM25) vs LLM Pretrained (MiniLM)
menggunakan ground truth yang telah didefinisikan.

Metrik yang dihitung:
  - Precision@K (K=5, 10, 20, 50)
  - Recall@K (K=5, 10, 20, 50)
  - F1-Score@K (K=5, 10, 20, 50)
  - Mean Average Precision (MAP)
  - Normalized Discounted Cumulative Gain (NDCG@K)

Visualisasi:
  - Grafik perbandingan metrik kinerja (@K)
  - Precision-Recall Curve (simulated or actual)
=============================================================
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# Path definition
BASE_DIR          = Path(__file__).resolve().parent
PATH_GT           = BASE_DIR / "data" / "ground_truth.csv"
PATH_BASELINE     = BASE_DIR.parent / "Tugas Final" / "data" / "output" / "hasil_siswa_berprestasi.json"
PATH_LLM          = BASE_DIR.parent / "Tugas Pembanding" / "data" / "output" / "hasil_siswa_berprestasi_llm.json"
OUTPUT_PLOT_DIR   = BASE_DIR / "plots"
OUTPUT_STATS_JSON = BASE_DIR / "data" / "evaluation_results.json"

def load_ground_truth() -> dict:
    """Load ground truth labels as dictionary {nama_siswa: relevance_label}."""
    if not PATH_GT.exists():
        raise FileNotFoundError(f"Ground Truth tidak ditemukan di: {PATH_GT}\nPastikan generate_ground_truth.py sudah dijalankan!")
    
    df = pd.read_csv(PATH_GT)
    return dict(zip(df["nama_siswa"], df["relevance_ground_truth"]))

def load_ranked_list(path: Path) -> list:
    """Load ranked student names from json output."""
    if not path.exists():
        raise FileNotFoundError(f"File hasil tidak ditemukan di: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [s["nama_siswa"] for s in data.get("students", [])]

def calculate_metrics(ranked_list: list, ground_truth: dict) -> dict:
    """
    Hitung metrik IR: Precision@K, Recall@K, F1@K, MAP, NDCG@K.
    """
    # Total dokumen relevan dalam ground truth
    total_relevan = sum(1 for v in ground_truth.values() if v == 1)
    
    if total_relevan == 0:
        return {}

    # Konversi ranked list ke biner relevance list
    # Jika siswa tidak ada di ground truth, anggap tidak relevan (0)
    binary_relevance = [ground_truth.get(name, 0) for name in ranked_list]

    metrics = {}
    ks = [5, 10, 20, 50]
    
    # 1. Precision@K, Recall@K, F1@K, NDCG@K
    for k in ks:
        k_val = min(k, len(binary_relevance))
        if k_val == 0:
            metrics[f"precision@{k}"] = 0.0
            metrics[f"recall@{k}"] = 0.0
            metrics[f"f1@{k}"] = 0.0
            metrics[f"ndcg@{k}"] = 0.0
            continue
            
        hits = sum(binary_relevance[:k_val])
        
        # Precision@K
        precision = hits / k_val
        metrics[f"precision@{k}"] = round(precision, 4)
        
        # Recall@K
        recall = hits / total_relevan
        metrics[f"recall@{k}"] = round(recall, 4)
        
        # F1@K
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0
        metrics[f"f1@{k}"] = round(f1, 4)
        
        # NDCG@K
        dcg = 0.0
        for i in range(k_val):
            rel = binary_relevance[i]
            dcg += rel / np.log2(i + 2) # i+2 karena 1-indexed i+1 dan index log2 dimulai dari 2
            
        # Ideal DCG (semua elemen top K adalah relevan)
        idcg = 0.0
        ideal_relevance = sorted(binary_relevance, reverse=True)
        for i in range(min(k_val, total_relevan)):
            idcg += 1.0 / np.log2(i + 2)
            
        metrics[f"ndcg@{k}"] = round(dcg / idcg, 4) if idcg > 0 else 0.0

    # 2. Mean Average Precision (MAP)
    # Karena kita hanya memiliki 1 query beasiswa tunggal, MAP = AP (Average Precision) query tersebut
    ap = 0.0
    num_relevan_found = 0
    for i, rel in enumerate(binary_relevance):
        if rel == 1:
            num_relevan_found += 1
            precision_at_i = num_relevan_found / (i + 1)
            ap += precision_at_i
            
    ap = ap / total_relevan if total_relevan > 0 else 0.0
    metrics["map"] = round(ap, 4)
    
    return metrics

def plot_comparison(baseline_metrics: dict, llm_metrics: dict):
    """Buat visualisasi perbandingan metrik kinerja dan simpan ke file."""
    OUTPUT_PLOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Bar plot perbandingan metrik umum @10 dan MAP
    comparison_keys = ["precision@10", "recall@10", "f1@10", "ndcg@10", "map", "precision@20", "recall@20", "f1@20", "ndcg@20"]
    
    plot_data = []
    for key in comparison_keys:
        plot_data.append({"Metric": key.upper(), "Score": baseline_metrics[key], "Method": "Baseline (TF-IDF + BM25)"})
        plot_data.append({"Metric": key.upper(), "Score": llm_metrics[key], "Method": "LLM (MiniLM)"})
        
    df_plot = pd.DataFrame(plot_data)
    
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 7))
    
    palette = {"Baseline (TF-IDF + BM25)": "#3498db", "LLM (MiniLM)": "#e74c3c"}
    
    ax = sns.barplot(
        data=df_plot, 
        x="Metric", 
        y="Score", 
        hue="Method", 
        palette=palette
    )
    
    # Add values on top of bars
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(f'{height:.3f}',
                        (p.get_x() + p.get_width() / 2., height + 0.01),
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
            
    plt.title("Perbandingan Kinerja Information Retrieval: Baseline vs LLM Pretrained", fontsize=14, fontweight='bold', pad=15)
    plt.ylim(0, 1.1)
    plt.ylabel("Score", fontsize=12)
    plt.xlabel("Evaluation Metric", fontsize=12)
    plt.xticks(rotation=15)
    plt.legend(loc='upper right', frameon=True, shadow=True)
    plt.tight_layout()
    
    plot_path = OUTPUT_PLOT_DIR / "ir_metrics_comparison.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    
    # 2. Line plot untuk Precision & Recall @K curves
    ks = [5, 10, 20, 50]
    p_base = [baseline_metrics[f"precision@{k}"] for k in ks]
    p_llm = [llm_metrics[f"precision@{k}"] for k in ks]
    r_base = [baseline_metrics[f"recall@{k}"] for k in ks]
    r_llm = [llm_metrics[f"recall@{k}"] for k in ks]
    
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(ks, p_base, marker='o', color='#3498db', label="Baseline", linewidth=2)
    plt.plot(ks, p_llm, marker='s', color='#e74c3c', label="LLM", linewidth=2)
    plt.title("Precision @ K Curve", fontsize=11, fontweight='bold')
    plt.xlabel("K")
    plt.ylabel("Precision")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(ks, r_base, marker='o', color='#2ecc71', label="Baseline", linewidth=2)
    plt.plot(ks, r_llm, marker='s', color='#27ae60', label="LLM", linewidth=2)
    plt.title("Recall @ K Curve", fontsize=11, fontweight='bold')
    plt.xlabel("K")
    plt.ylabel("Recall")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plt.tight_layout()
    plot_curve_path = OUTPUT_PLOT_DIR / "precision_recall_curves.png"
    plt.savefig(plot_curve_path, dpi=300)
    plt.close()
    
    print(Fore.GREEN + f"  ✔ Grafik evaluasi disimpan di folder: {OUTPUT_PLOT_DIR}")

def main():
    print(Fore.BLUE + Style.BRIGHT + """
╔═══════════════════════════════════════════════════════════╗
║   EVALUASI METRIK KINERJA RETRIEVAL (BASELINE VS LLM)     ║
║   Precision, Recall, F1, MAP, NDCG                        ║
╚═══════════════════════════════════════════════════════════╝
""")

    try:
        ground_truth = load_ground_truth()
        baseline_ranked = load_ranked_list(PATH_BASELINE)
        llm_ranked = load_ranked_list(PATH_LLM)
    except FileNotFoundError as e:
        print(Fore.RED + f"[ERROR] {e}")
        print(Fore.RED + "Pastikan generate_ground_truth.py, pipeline Tugas Final & Tugas Pembanding telah dijalankan!")
        return

    print(Fore.CYAN + "  Menghitung metrik untuk Baseline (TF-IDF + BM25)...")
    baseline_metrics = calculate_metrics(baseline_ranked, ground_truth)

    print(Fore.CYAN + "  Menghitung metrik untuk LLM Pretrained (MiniLM)...")
    llm_metrics = calculate_metrics(llm_ranked, ground_truth)

    if not baseline_metrics or not llm_metrics:
        print(Fore.RED + "[ERROR] Gagal menghitung metrik.")
        return

    # Print hasil perbandingan
    print(Fore.BLUE + Style.BRIGHT + "\n=== HASIL EVALUASI METRIK RETRIEVAL ===")
    
    header = f"{'Metric':<15} | {'Baseline (TF-IDF+BM25)':<22} | {'LLM (MiniLM)':<15} | {'Perbedaan':<10}"
    print(Fore.YELLOW + Style.BRIGHT + header)
    print("-" * 72)
    
    for key in sorted(baseline_metrics.keys()):
        val_base = baseline_metrics[key]
        val_llm = llm_metrics[key]
        diff = val_llm - val_base
        diff_str = f"{diff:+.4f}" if diff != 0 else "0.0000"
        
        color = Fore.GREEN if diff > 0 else Fore.RED if diff < 0 else Fore.WHITE
        
        print(f"{key:<15} | {val_base:<22.4f} | {val_llm:<15.4f} | {color}{diff_str}")
        
    print("-" * 72)

    # Simpan visualisasi
    plot_comparison(baseline_metrics, llm_metrics)

    # Simpan hasil metrik ke JSON
    eval_results = {
        "metadata": {
            "evaluation_time": datetime.now().isoformat(),
            "total_ground_truth_relevant": sum(1 for v in ground_truth.values() if v == 1),
            "total_candidates": len(ground_truth)
        },
        "baseline_metrics": baseline_metrics,
        "llm_metrics": llm_metrics,
        "metric_differences": {k: round(llm_metrics[k] - baseline_metrics[k], 4) for k in baseline_metrics.keys()}
    }

    OUTPUT_STATS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_STATS_JSON, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)
    print(Fore.GREEN + f"\n  ✔ Statistik evaluasi lengkap disimpan ke: {OUTPUT_STATS_JSON}\n")

if __name__ == "__main__":
    main()
