"""
=============================================================
STEP 5 - SCORING AKHIR & EXPORT HASIL
=============================================================
Referensi:
  - Salton, G. & Buckley, C. (1988). Term-weighting approaches in
    automatic text retrieval. IPM. (Scopus Q1)
  - Baeza-Yates, R. & Ribeiro-Neto, B. (2011). Modern Information
    Retrieval. 2nd ed. Ch. 3 — Ranking.
  - Wahyudi, A. et al. (2019). Implementasi TF-IDF pada Sistem
    Rekomendasi Beasiswa. JATI. (Scopus indexed)
  
Output akhir:
  - data/output/hasil_siswa_berprestasi.json
  - data/output/hasil_siswa_berprestasi.csv
  - data/output/top100_siswa.csv
=============================================================
"""

import json
import csv
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

BASE_DIR    = Path(__file__).resolve().parent.parent
INPUT_PATH  = BASE_DIR / "data" / "processed" / "step4_indexed.json"
OUT_JSON    = BASE_DIR / "data" / "output" / "hasil_siswa_berprestasi.json"
OUT_CSV     = BASE_DIR / "data" / "output" / "hasil_siswa_berprestasi.csv"
OUT_TOP100  = BASE_DIR / "data" / "output" / "top100_siswa_beasiswa.csv"


# ─── Bobot skor tingkat kompetisi ─────────────────────────────────────────────
LEVEL_WEIGHTS = {
    "Internasional"    : 1.00,
    "Nasional"         : 0.85,
    "Provinsi"         : 0.65,
    "Kota/Kabupaten"   : 0.45,
    "Sekolah/Kecamatan": 0.25,
    None               : 0.30,  # default jika tidak diketahui
}


def compute_final_score(student: dict) -> float:
    """
    Hitung skor akhir siswa untuk rekomendasi beasiswa.
    
    Final Score = cosine_similarity × level_weight × frequency_bonus
    
    Komponen:
      cosine_similarity : skor relevansi dari TF-IDF + BM25
      level_weight      : bobot berdasarkan tingkat kompetisi
      frequency_bonus   : bonus jika muncul di banyak post (min 1.0, max 1.2)
    """
    cosine  = student.get("cosine_similarity", 0)
    tingkat = student.get("tingkat_kompetisi")
    n_posts = student.get("jumlah_post", 1)

    level_w = LEVEL_WEIGHTS.get(tingkat, 0.30)

    # Bonus frekuensi: 1.0 + min(0.2, 0.05 × (n_posts - 1))
    freq_bonus = 1.0 + min(0.20, 0.05 * (n_posts - 1))

    return round(cosine * level_w * freq_bonus, 6)


def classify_student(student: dict) -> str:
    """
    Klasifikasikan siswa berdasarkan skor akhir.
    """
    score = student.get("final_score", 0)
    if score >= 0.20:
        return "SANGAT DIREKOMENDASIKAN"
    elif score >= 0.10:
        return "DIREKOMENDASIKAN"
    elif score >= 0.05:
        return "PERTIMBANGKAN"
    else:
        return "PERLU VERIFIKASI"


def enrich_student(student: dict, rank: int) -> dict:
    """Tambahkan field tambahan untuk output akhir."""
    final_score = compute_final_score(student)
    student["rank"]          = rank
    student["final_score"]   = final_score
    student["rekomendasi"]   = classify_student({**student, "final_score": final_score})
    student["generated_at"]  = datetime.now().isoformat()
    return student


def export_csv(students: list, path: Path, top_n: int = None):
    """Export ke CSV format."""
    if top_n:
        students = students[:top_n]

    rows = []
    for s in students:
        rows.append({
            "Rank"               : s.get("rank"),
            "Nama Siswa"         : s.get("nama_siswa", "-"),
            "Sekolah"            : s.get("sekolah", "-"),
            "Provinsi"           : s.get("provinsi", "-"),
            "Bidang"             : s.get("bidang", "-"),
            "Prestasi"           : s.get("prestasi", "-"),
            "Tingkat"            : s.get("tingkat_kompetisi", "-"),
            "Cosine Similarity"  : s.get("cosine_similarity"),
            "TF-IDF Score"       : s.get("tfidf_score"),
            "BM25 Score"         : s.get("bm25_score"),
            "Final Score"        : s.get("final_score"),
            "Rekomendasi"        : s.get("rekomendasi"),
            "Jumlah Post"        : s.get("jumlah_post", 1),
            "Total Likes"        : s.get("total_likes", 0),
            "Post URL"           : s.get("best_post_url", "-"),
            "Caption (snippet)"  : s.get("best_post_snippet", "-")[:100],
        })

    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(Fore.GREEN + f"  ✔ CSV disimpan: {path}")
    return df


def print_top_results(students: list, n: int = 20):
    """Tampilkan tabel top-N hasil."""
    print(Fore.BLUE + Style.BRIGHT + "\n" + "=" * 100)
    print(Fore.BLUE + Style.BRIGHT + "  HASIL AKHIR: TOP SISWA SMA BERPRESTASI (KANDIDAT BEASISWA)")
    print(Fore.BLUE + Style.BRIGHT + "=" * 100)
    print(
        Fore.YELLOW + Style.BRIGHT +
        f"{'Rank':>4}  {'Nama Siswa':<28} {'Sekolah':<25} {'Bidang':<18} "
        f"{'Cosine':>7} {'BM25':>7} {'TF-IDF':>7} {'Final':>7} {'Rekomendasi'}"
    )
    print(Fore.WHITE + "-" * 100)

    for s in students[:n]:
        color = {
            "SANGAT DIREKOMENDASIKAN": Fore.GREEN,
            "DIREKOMENDASIKAN"       : Fore.CYAN,
            "PERTIMBANGKAN"          : Fore.YELLOW,
            "PERLU VERIFIKASI"       : Fore.RED,
        }.get(s.get("rekomendasi"), Fore.WHITE)

        print(
            color +
            f"{s['rank']:>4}  "
            f"{str(s.get('nama_siswa', '-')):<28} "
            f"{str(s.get('sekolah', '-'))[:25]:<25} "
            f"{str(s.get('bidang', '-'))[:18]:<18} "
            f"{s.get('cosine_similarity', 0):>7.4f} "
            f"{s.get('bm25_score', 0):>7.4f} "
            f"{s.get('tfidf_score', 0):>7.4f} "
            f"{s.get('final_score', 0):>7.4f} "
            f"{s.get('rekomendasi', '-')}"
        )

    print(Fore.WHITE + "-" * 100)


def main():
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)
    print(Fore.BLUE + Style.BRIGHT + "  STEP 5: SCORING AKHIR & EXPORT")
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    students = data.get("ranked_students", [])
    print(Fore.CYAN + f"[STEP 5] Menghitung skor akhir {len(students):,} siswa...")

    # Hitung final score & enrichment
    enriched = []
    for i, s in enumerate(students):
        es = enrich_student(s, rank=i + 1)
        enriched.append(es)

    # Re-sort berdasarkan final_score
    enriched.sort(key=lambda s: s["final_score"], reverse=True)
    for i, s in enumerate(enriched):
        s["rank"] = i + 1

    # ─── Statistik ────────────────────────────────────────────────
    rekomendasi_counts = {}
    for s in enriched:
        r = s["rekomendasi"]
        rekomendasi_counts[r] = rekomendasi_counts.get(r, 0) + 1

    print(Fore.CYAN + "\n  Distribusi Rekomendasi:")
    for k, v in rekomendasi_counts.items():
        print(f"    {k:<28}: {v:,}")

    # ─── Tampilkan tabel ───────────────────────────────────────────
    print_top_results(enriched, n=30)

    # ─── Export ───────────────────────────────────────────────────
    final_output = {
        "metadata": {
            "generated_at"        : datetime.now().isoformat(),
            "total_students"      : len(enriched),
            "query"               : data.get("summary", {}).get("query"),
            "indexing_weights"    : data.get("summary", {}).get("indexing_weights"),
            "level_weights"       : LEVEL_WEIGHTS,
            "rekomendasi_counts"  : rekomendasi_counts,
        },
        "students": enriched,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    print(Fore.GREEN + f"\n  ✔ JSON disimpan: {OUT_JSON}")

    export_csv(enriched, OUT_CSV)
    export_csv(enriched, OUT_TOP100, top_n=100)

    print(Fore.GREEN + Style.BRIGHT + "\n  ✔ STEP 5 SELESAI")
    print(Fore.GREEN + Style.BRIGHT + f"  ✔ Lihat hasil: {OUT_TOP100}\n")
    return enriched


if __name__ == "__main__":
    main()
