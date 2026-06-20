"""
=============================================================
QUICK RUN - Langsung dari data yang sudah ada (data.json)
=============================================================
Script ini menjalankan pipeline langsung dari data yang sudah
diproses di Tugas 1 (data.json berisi nama_siswa, sekolah, dll)
tanpa perlu re-crawl dari Apify.

Ini adalah inti dari tugas final: Indexing + Scoring + Ranking
=============================================================
"""

import json
import math
import re
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
from rank_bm25 import BM25Okapi

init(autoreset=True)

BASE_DIR        = Path(__file__).parent
DATA_INPUT      = BASE_DIR / "data" / "processed" / "data_preprocessed.json"
OUTPUT_JSON     = BASE_DIR / "data" / "output" / "hasil_siswa_berprestasi.json"
OUTPUT_CSV      = BASE_DIR / "data" / "output" / "hasil_siswa_berprestasi.csv"
OUTPUT_TOP100   = BASE_DIR / "data" / "output" / "top100_siswa_beasiswa.csv"

# ─── Query pencarian beasiswa ──────────────────────────────────────────────────
QUERY = (
    "siswa berprestasi juara olimpiade sains nasional osn beasiswa sma "
    "medali emas perak prestasi akademik terbaik kompetisi unggul "
    "juara pertama kedua ketiga lomba nasional internasional "
    "kelas xi sma sman smk madrasah aliyah"
)

LEVEL_WEIGHTS = {
    "Internasional"    : 1.00,
    "Nasional"         : 0.85,
    "Provinsi"         : 0.65,
    "Kota/Kabupaten"   : 0.45,
    "Sekolah/Kecamatan": 0.25,
    None               : 0.30,
}

STOPWORDS_ID = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
    "pada", "adalah", "atau", "dalam", "tidak", "juga", "sudah", "saya",
    "kita", "kami", "mereka", "akan", "bisa", "ada", "oleh", "atas",
    "sebagai", "telah", "dapat", "nya", "lah", "pun", "lebih", "sangat",
    "serta", "setelah", "sebelum", "agar", "karena", "namun", "tetapi",
    "jika", "ketika", "hingga", "antara", "setiap", "semua", "para",
    "maka", "sedang", "bagi", "demi", "tanpa", "lagi", "belum", "harus",
    "perlu", "baru", "masih", "selalu", "hanya", "saja", "terus",
    "ya", "yg", "dgn", "dr", "utk", "krn", "tdk",
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#(\w+)", r"\1", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    tokens = [t for t in text.split() if t not in STOPWORDS_ID and len(t) > 1]
    return " ".join(tokens)


def load_data() -> list:
    """Load data dari data_preprocessed.json (data.json dari Tugas 1)."""
    with open(DATA_INPUT, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Support format langsung array atau {"rows": [...]}
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        rows = raw.get("rows", raw.get("posts", []))
    else:
        rows = []

    print(Fore.CYAN + f"  Data dimuat: {len(rows):,} record")
    return rows


def run_pipeline(rows: list) -> list:
    """Pipeline lengkap: NLP → TF-IDF → BM25 → Cosine → Ranking."""

    # ─── 1. Filter hanya yang punya nama siswa ───────────────────
    with_name = [r for r in rows if r.get("nama_siswa") and len(str(r["nama_siswa"])) > 2]
    print(Fore.CYAN + f"  Record dengan nama_siswa: {len(with_name):,}")

    # ─── 2. Buat corpus dokumen ───────────────────────────────────
    corpus_clean = []
    for r in with_name:
        text = f"{r.get('caption', '')} {r.get('nama_siswa', '')} {r.get('sekolah', '')} {r.get('bidang', '')} {r.get('juara', '')}"
        corpus_clean.append(clean_text(text))

    tokenized_corpus = [doc.split() for doc in corpus_clean]
    query_clean      = clean_text(QUERY)

    # ─── 3. TF-IDF ───────────────────────────────────────────────
    print(Fore.CYAN + "\n  Menghitung TF-IDF...")
    vectorizer = TfidfVectorizer(
        sublinear_tf=True,
        min_df=1,
        max_df=0.95,
        ngram_range=(1, 2),
    )
    all_texts    = corpus_clean + [query_clean]
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    doc_matrix   = tfidf_matrix[:-1]
    query_vec    = tfidf_matrix[-1]
    tfidf_scores = sk_cosine(query_vec, doc_matrix).flatten()
    print(Fore.GREEN + f"  ✔ TF-IDF vocab: {len(vectorizer.vocabulary_):,} terms")

    # ─── 4. BM25 ─────────────────────────────────────────────────
    print(Fore.CYAN + "  Menghitung BM25...")
    bm25         = BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)
    query_tokens = query_clean.split()
    bm25_raw     = np.array(bm25.get_scores(query_tokens))
    bm25_max     = bm25_raw.max()
    bm25_scores  = bm25_raw / bm25_max if bm25_max > 0 else bm25_raw
    print(Fore.GREEN + f"  ✔ BM25 max score: {bm25_max:.4f}")

    # ─── 5. Engagement score ──────────────────────────────────────
    eng_raw   = np.array([math.log1p(max(0, r.get("likes", 0) or 0)) for r in with_name])
    eng_max   = eng_raw.max()
    eng_scores = eng_raw / eng_max if eng_max > 0 else eng_raw

    # ─── 6. Combined cosine similarity ───────────────────────────
    combined = (0.40 * tfidf_scores) + (0.45 * bm25_scores) + (0.15 * eng_scores)

    # ─── 7. Tambah skor ke data ───────────────────────────────────
    for i, r in enumerate(with_name):
        r["_tfidf_score"]    = float(tfidf_scores[i])
        r["_bm25_score"]     = float(bm25_scores[i])
        r["_eng_score"]      = float(eng_scores[i])
        r["_cosine_combined"] = float(combined[i])

    # ─── 8. Agregasi per nama siswa ───────────────────────────────
    from collections import defaultdict
    student_map = defaultdict(list)
    for r in with_name:
        name = str(r["nama_siswa"]).strip()
        student_map[name].append(r)

    students = []
    for name, records in student_map.items():
        best    = max(records, key=lambda r: r["_cosine_combined"])
        tingkat = best.get("tingkat") or best.get("signals", {}).get("tingkat") if isinstance(best.get("signals"), dict) else None
        lw      = LEVEL_WEIGHTS.get(tingkat, 0.30)
        n_posts = len(records)
        freq_b  = 1.0 + min(0.20, 0.05 * (n_posts - 1))
        cosine  = best["_cosine_combined"]
        final   = round(cosine * lw * freq_b, 6)

        if final >= 0.20: reko = "SANGAT DIREKOMENDASIKAN"
        elif final >= 0.10: reko = "DIREKOMENDASIKAN"
        elif final >= 0.05: reko = "PERTIMBANGKAN"
        else: reko = "PERLU VERIFIKASI"

        students.append({
            "nama_siswa"         : name,
            "sekolah"            : best.get("sekolah"),
            "provinsi"           : best.get("provinsi"),
            "bidang"             : best.get("bidang"),
            "prestasi"           : best.get("juara"),
            "tingkat_kompetisi"  : tingkat,
            "cosine_similarity"  : round(cosine, 6),
            "tfidf_score"        : round(best["_tfidf_score"], 6),
            "bm25_score"         : round(best["_bm25_score"], 6),
            "final_score"        : final,
            "rekomendasi"        : reko,
            "jumlah_post"        : n_posts,
            "total_likes"        : sum(r.get("likes", 0) or 0 for r in records),
            "kelas_xi"           : best.get("kelas_xi", False),
            "best_post_url"      : best.get("url"),
            "caption_snippet"    : str(best.get("caption", ""))[:150],
        })

    students.sort(key=lambda s: s["final_score"], reverse=True)
    for i, s in enumerate(students):
        s["rank"] = i + 1

    return students


def print_table(students: list, n: int = 30):
    """Print tabel hasil di terminal."""
    print(Fore.BLUE + Style.BRIGHT + "\n" + "═" * 110)
    print(Fore.BLUE + Style.BRIGHT + "  HASIL AKHIR: SISWA SMA BERPRESTASI — KANDIDAT BEASISWA")
    print(Fore.BLUE + Style.BRIGHT + "═" * 110)
    h = f"{'#':>3}  {'Nama Siswa':<26} {'Sekolah':<22} {'Bidang':<16} {'Tingkat':<12} {'Cosine':>7} {'BM25':>6} {'Final':>7}  Rekomendasi"
    print(Fore.YELLOW + Style.BRIGHT + h)
    print(Fore.WHITE + "─" * 110)

    for s in students[:n]:
        clr = {
            "SANGAT DIREKOMENDASIKAN": Fore.GREEN,
            "DIREKOMENDASIKAN"       : Fore.CYAN,
            "PERTIMBANGKAN"          : Fore.YELLOW,
            "PERLU VERIFIKASI"       : Fore.RED,
        }.get(s["rekomendasi"], Fore.WHITE)

        print(clr + (
            f"{s['rank']:>3}  "
            f"{str(s['nama_siswa'])[:26]:<26} "
            f"{str(s['sekolah'] or '-')[:22]:<22} "
            f"{str(s['bidang'] or '-')[:16]:<16} "
            f"{str(s['tingkat_kompetisi'] or '-')[:12]:<12} "
            f"{s['cosine_similarity']:>7.4f} "
            f"{s['bm25_score']:>6.4f} "
            f"{s['final_score']:>7.4f}  "
            f"{s['rekomendasi']}"
        ))
    print(Fore.WHITE + "─" * 110)


def main():
    print(Fore.BLUE + Style.BRIGHT + """
╔═══════════════════════════════════════════════════════════╗
║   QUICK RUN — IR Pipeline (Data Preprocessed)            ║
║   NER + TF-IDF + BM25 + Cosine Similarity               ║
╚═══════════════════════════════════════════════════════════╝
""")

    print(Fore.CYAN + "[1/4] Loading data...")
    rows = load_data()

    print(Fore.CYAN + "\n[2/4] Menjalankan pipeline NLP + Indexing...")
    students = run_pipeline(rows)

    print(Fore.CYAN + "\n[3/4] Menampilkan hasil...")
    print_table(students, n=30)

    # Stats
    dist = {}
    for s in students:
        dist[s["rekomendasi"]] = dist.get(s["rekomendasi"], 0) + 1
    print(Fore.CYAN + "\n  Distribusi Rekomendasi:")
    for k, v in dist.items():
        print(f"    {k:<28}: {v}")

    print(Fore.CYAN + f"\n[4/4] Menyimpan output...")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_students": len(students),
                "query": QUERY,
                "metode": "TF-IDF + BM25 + Cosine Similarity",
                "indexing_weights": {"tfidf": 0.40, "bm25": 0.45, "engagement": 0.15},
            },
            "students": students,
        }, f, ensure_ascii=False, indent=2)
    print(Fore.GREEN + f"  ✔ JSON → {OUTPUT_JSON}")

    # CSV full
    df = pd.DataFrame([{
        "Rank"              : s["rank"],
        "Nama Siswa"        : s["nama_siswa"],
        "Sekolah"           : s["sekolah"],
        "Provinsi"          : s["provinsi"],
        "Bidang"            : s["bidang"],
        "Prestasi"          : s["prestasi"],
        "Tingkat"           : s["tingkat_kompetisi"],
        "Cosine Similarity" : s["cosine_similarity"],
        "TF-IDF Score"      : s["tfidf_score"],
        "BM25 Score"        : s["bm25_score"],
        "Final Score"       : s["final_score"],
        "Rekomendasi"       : s["rekomendasi"],
        "Jumlah Post"       : s["jumlah_post"],
        "Total Likes"       : s["total_likes"],
        "Kelas XI"          : s["kelas_xi"],
        "URL Post"          : s["best_post_url"],
    } for s in students])

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(Fore.GREEN + f"  ✔ CSV → {OUTPUT_CSV}")

    df.head(100).to_csv(OUTPUT_TOP100, index=False, encoding="utf-8-sig")
    print(Fore.GREEN + f"  ✔ Top 100 → {OUTPUT_TOP100}")

    print(Fore.GREEN + Style.BRIGHT + "\n  ✔ PIPELINE SELESAI!\n")
    return students


if __name__ == "__main__":
    main()
