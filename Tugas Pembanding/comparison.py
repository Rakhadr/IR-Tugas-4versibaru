"""
=============================================================
TUGAS PEMBANDING - ANALYSIS & COMPARISON SCRIPT
=============================================================
Menganalisis kemiripan pembobotan dan peringkat antara:
  - Baseline (TF-IDF + BM25)
  - LLM Pretrained Dense Embedding (MiniLM)

Metrik Perbandingan:
  - Korelasi Peringkat Spearman (Spearman's Rho)
  - Korelasi Peringkat Kendall (Kendall's Tau)
  - Jaccard Similarity / Overlap pada Top K (K=10, 20, 50)
  - Visualisasi pergeseran peringkat (Rank Drift)
=============================================================
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from colorama import Fore, Style, init
from scipy.stats import spearmanr, kendalltau

init(autoreset=True)

# Path definition
BASE_DIR        = Path(__file__).resolve().parent
PATH_BASELINE   = BASE_DIR.parent / "Tugas Final" / "data" / "output" / "hasil_siswa_berprestasi.json"
PATH_LLM        = BASE_DIR / "data" / "output" / "hasil_siswa_berprestasi_llm.json"
OUTPUT_COMP_CSV = BASE_DIR / "data" / "output" / "perbandingan_peringkat.csv"

def load_results(path: Path) -> dict:
    """Load list of students from json."""
    if not path.exists():
        raise FileNotFoundError(f"File hasil tidak ditemukan di: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {s["nama_siswa"]: s for s in data.get("students", [])}

def compute_jaccard(list_a, list_b):
    """Hitung overlap Jaccard similarity antara dua set."""
    set_a = set(list_a)
    set_b = set(list_b)
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def main():
    print(Fore.BLUE + Style.BRIGHT + """
╔═══════════════════════════════════════════════════════════╗
║   ANALISIS PERBANDINGAN PERINGKAT: BASELINE vs LLM        ║
║   Spearman & Kendall correlation + Rank Overlap           ║
╚═══════════════════════════════════════════════════════════╝
""")

    try:
        baseline_students = load_results(PATH_BASELINE)
        llm_students = load_results(PATH_LLM)
    except FileNotFoundError as e:
        print(Fore.RED + f"[ERROR] {e}")
        print(Fore.RED + "Pastikan kedua pipeline (Tugas Final & Tugas Pembanding) telah dijalankan terlebih dahulu!")
        return

    common_names = list(set(baseline_students.keys()).intersection(set(llm_students.keys())))
    print(Fore.CYAN + f"  Jumlah siswa terdaftar di Baseline : {len(baseline_students)}")
    print(Fore.CYAN + f"  Jumlah siswa terdaftar di LLM      : {len(llm_students)}")
    print(Fore.CYAN + f"  Jumlah irisan siswa (common)      : {len(common_names)}")

    if not common_names:
        print(Fore.RED + "[ERROR] Tidak ada nama siswa yang sama di kedua dataset!")
        return

    # 1. Hitung korelasi peringkat
    # Ambil peringkat untuk setiap siswa yang ada di kedua metode
    ranks_baseline = []
    ranks_llm = []
    scores_baseline = []
    scores_llm = []

    comparison_data = []

    for name in common_names:
        s_base = baseline_students[name]
        s_llm = llm_students[name]
        
        ranks_baseline.append(s_base["rank"])
        ranks_llm.append(s_llm["rank"])
        scores_baseline.append(s_base["final_score"])
        scores_llm.append(s_llm["final_score"])
        
        comparison_data.append({
            "Nama Siswa": name,
            "Sekolah": s_base.get("sekolah", "-"),
            "Rank Baseline": s_base["rank"],
            "Rank LLM": s_llm["rank"],
            "Rank Drift": s_base["rank"] - s_llm["rank"], # Positif berarti LLM meranking lebih tinggi (angka rank lebih kecil)
            "Score Baseline": s_base["final_score"],
            "Score LLM": s_llm["final_score"],
            "Rekomendasi Baseline": s_base["rekomendasi"],
            "Rekomendasi LLM": s_llm["rekomendasi"]
        })

    # Urutkan data perbandingan berdasarkan Rank Baseline
    df_comp = pd.DataFrame(comparison_data).sort_values("Rank Baseline")

    # Spearman's rank correlation
    spearman_corr, spearman_p = spearmanr(ranks_baseline, ranks_llm)
    # Kendall's tau rank correlation
    kendall_corr, kendall_p = kendalltau(ranks_baseline, ranks_llm)
    # Pearson correlation on final scores
    pearson_corr = np.corrcoef(scores_baseline, scores_llm)[0, 1]

    print(Fore.BLUE + Style.BRIGHT + "\n=== STATISTIK KORELASI PERINGKAT ===")
    print(f"  Spearman's Rank Correlation (Rho) : {spearman_corr:.4f} (p-value: {spearman_p:.2e})")
    print(f"  Kendall's Rank Correlation (Tau)   : {kendall_corr:.4f} (p-value: {kendall_p:.2e})")
    print(f"  Pearson Score Correlation          : {pearson_corr:.4f}")
    print(Fore.WHITE + "-" * 60)
    print(Fore.YELLOW + "Interpretasi:")
    if spearman_corr > 0.8:
        print("  - Korelasi SANGAT KUAT: Kedua metode memberikan pembobotan dan peringkat yang hampir identik.")
    elif spearman_corr > 0.5:
        print("  - Korelasi SEDANG-KUAT: Peringkat mirip, namun ada pergeseran signifikan pada beberapa siswa.")
    elif spearman_corr > 0.2:
        print("  - Korelasi LEMAH: Ada kemiripan tren umum, tetapi pembobotan lokal sangat berbeda.")
    else:
        print("  - Korelasi SANGAT LEMAH / TIDAK ADA: Kedua metode meranking siswa secara acak/berbeda total.")

    # 2. Rank Overlap (Jaccard Similarity) pada Top K
    # Urutkan semua siswa dari JSON asli berdasarkan rank
    top_baseline_names = sorted(baseline_students.keys(), key=lambda k: baseline_students[k]["rank"])
    top_llm_names = sorted(llm_students.keys(), key=lambda k: llm_students[k]["rank"])

    print(Fore.BLUE + Style.BRIGHT + "\n=== RANK OVERLAP ANALYSIS (JACCARD SIMILARITY) ===")
    for k in [5, 10, 20, 50]:
        base_k = top_baseline_names[:k]
        llm_k = top_llm_names[:k]
        jaccard = compute_jaccard(base_k, llm_k)
        overlap_count = len(set(base_k).intersection(set(llm_k)))
        print(f"  Top-{k:<2} Overlap: {overlap_count}/{k} siswa ({jaccard * 100:.1f}% Jaccard Similarity)")

    # 3. Print Top 15 Side-by-Side Comparison
    print(Fore.BLUE + Style.BRIGHT + "\n=== PERBANDINGAN TOP 15 SISWA (SIDE-BY-SIDE) ===")
    print(f"{'Rank':<4} | {'Baseline (TF-IDF + BM25)':<32} | {'LLM Pretrained Embedding (MiniLM)':<32}")
    print("-" * 76)
    for r in range(1, 16):
        name_base = top_baseline_names[r-1] if r-1 < len(top_baseline_names) else "-"
        name_llm = top_llm_names[r-1] if r-1 < len(top_llm_names) else "-"
        
        # Cari score masing-masing
        score_base = baseline_students[name_base]["final_score"] if name_base != "-" else 0.0
        score_llm = llm_students[name_llm]["final_score"] if name_llm != "-" else 0.0
        
        print(f"{r:<4} | {f'{name_base[:24]} ({score_base:.3f})':<32} | {f'{name_llm[:24]} ({score_llm:.3f})':<32}")
    print("-" * 76)

    # 4. Save perbandingan ke CSV
    df_comp.to_csv(OUTPUT_COMP_CSV, index=False, encoding="utf-8-sig")
    print(Fore.GREEN + f"\n  ✔ File perbandingan peringkat disimpan ke: {OUTPUT_COMP_CSV}")

    # Save stats summary JSON
    summary_path = BASE_DIR / "data" / "output" / "rank_comparison.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "spearman": {"correlation": float(spearman_corr), "p_value": float(spearman_p)},
            "kendall": {"correlation": float(kendall_corr), "p_value": float(kendall_p)},
            "pearson_score": float(pearson_corr),
            "jaccard_similarity": {
                "top5": float(compute_jaccard(top_baseline_names[:5], top_llm_names[:5])),
                "top10": float(compute_jaccard(top_baseline_names[:10], top_llm_names[:10])),
                "top20": float(compute_jaccard(top_baseline_names[:20], top_llm_names[:20])),
                "top50": float(compute_jaccard(top_baseline_names[:50], top_llm_names[:50])),
            }
        }, f, indent=2)
    print(Fore.GREEN + f"  ✔ File summary JSON disimpan ke: {summary_path}\n")

if __name__ == "__main__":
    main()
