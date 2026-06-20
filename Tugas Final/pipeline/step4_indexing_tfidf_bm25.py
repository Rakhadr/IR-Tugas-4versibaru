"""
=============================================================
STEP 4 - INDEXING: TF-IDF & BM25
=============================================================
Referensi:
  - Sparck Jones, K. (1972). A statistical interpretation of term
    specificity and its application in retrieval. JDoc. (Scopus Q1)
  - Robertson, S. E. & Walker, S. (1994). Some simple effective 
    approximations to the 2-Poisson model for probabilistic IR.
    SIGIR '94. (ACM, Scopus Q1) — Cikal bakal BM25
  - Robertson, S. & Zaragoza, H. (2009). The Probabilistic Relevance
    Framework: BM25 and Beyond. FTIR. (Scopus Q1)
  - Manning, C. D. et al. (2008). Introduction to Information
    Retrieval. Cambridge University Press. Ch. 6, 11.

Formula:
  TF-IDF  : w(t,d) = tf(t,d) × log(N / df(t))
  BM25    : Σ IDF(t) × [tf(t,d)(k1+1)] / [tf(t,d) + k1(1-b+b·|d|/avgdl)]
    k1=1.5, b=0.75 (default BM25 parameters)
=============================================================
"""

import json
import math
import numpy as np
from collections import Counter, defaultdict
from pathlib import Path
from colorama import Fore, Style, init
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi

init(autoreset=True)

BASE_DIR    = Path(__file__).resolve().parent.parent
INPUT_PATH  = BASE_DIR / "data" / "processed" / "step3_ner.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "step4_indexed.json"

# ─── Query relevansi: kriteria siswa berprestasi beasiswa ─────────────────────
SCHOLARSHIP_QUERY = (
    "siswa berprestasi juara olimpiade sains nasional osn beasiswa sma "
    "medali emas perak prestasi akademik terbaik kompetisi unggul "
    "juara pertama kedua ketiga lomba nasional internasional"
)


def build_corpus(posts: list) -> tuple:
    """
    Bangun corpus dokumen dari caption post.
    Returns: (corpus_texts, corpus_ids)
    """
    corpus_texts = []
    corpus_ids   = []

    for post in posts:
        tokens = post.get("tokens", [])
        if tokens:
            corpus_texts.append(" ".join(tokens))
            corpus_ids.append(post["id"])

    return corpus_texts, corpus_ids


def compute_tfidf(corpus: list, query: str) -> np.ndarray:
    """
    Hitung TF-IDF similarity menggunakan sklearn TfidfVectorizer.
    
    Implementasi: TF-IDF dengan smooth IDF (Sklearn default)
    tf-idf(t,d) = tf(t,d) × (log((1+n)/(1+df(t))) + 1)
    
    Cosine similarity dihitung antara query vector dan setiap dokumen.
    """
    print(Fore.CYAN + "  [TF-IDF] Fitting vectorizer...")

    vectorizer = TfidfVectorizer(
        sublinear_tf=True,     # Log normalization untuk TF
        min_df=1,
        max_df=0.95,
        ngram_range=(1, 2),    # Unigram + bigram
        analyzer="word",
    )

    # Fit pada corpus + query
    all_docs = corpus + [query]
    tfidf_matrix = vectorizer.fit_transform(all_docs)

    # Dokumen matrix (tanpa query)
    doc_matrix   = tfidf_matrix[:-1]
    query_vector = tfidf_matrix[-1]

    # Cosine similarity = dot(q, d) / (|q| × |d|)
    # Karena TF-IDF sudah L2-normalized di sklearn, cosine = dot product
    from sklearn.metrics.pairwise import cosine_similarity
    scores = cosine_similarity(query_vector, doc_matrix).flatten()

    print(Fore.GREEN + f"  [TF-IDF] ✔ Vocab size: {len(vectorizer.vocabulary_):,}")
    print(Fore.GREEN + f"  [TF-IDF] ✔ Score range: [{scores.min():.4f} – {scores.max():.4f}]")

    return scores, vectorizer


def compute_bm25(tokenized_corpus: list, query_tokens: list) -> np.ndarray:
    """
    Hitung BM25 score menggunakan rank_bm25 library.
    
    BM25 Okapi Parameters:
      k1 = 1.5  (kontrol saturasi term frequency)
      b  = 0.75 (kontrol normalisasi panjang dokumen)
    
    Referensi: Robertson & Zaragoza (2009). FTIR. Scopus Q1.
    """
    print(Fore.CYAN + "  [BM25] Membangun indeks BM25...")

    bm25 = BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)
    scores = np.array(bm25.get_scores(query_tokens))

    # Normalisasi ke [0, 1]
    max_score = scores.max()
    if max_score > 0:
        scores = scores / max_score

    print(Fore.GREEN + f"  [BM25] ✔ Score range: [{scores.min():.4f} – {scores.max():.4f}]")
    return scores


def compute_engagement_score(post: dict) -> float:
    """
    Skor engagement Instagram sebagai bobot tambahan.
    Engagement = (likes + comments × 2) / (1 + followers_estimated)
    Karena followers tidak tersedia, gunakan raw engagement.
    
    Dinormalisasi log untuk mengurangi bias outlier.
    """
    likes    = max(0, post.get("likesCount", 0) or 0)
    comments = max(0, post.get("commentsCount", 0) or 0)
    raw      = likes + (comments * 2)
    # Log normalisasi
    return math.log1p(raw)


def combine_scores(
    tfidf_scores : np.ndarray,
    bm25_scores  : np.ndarray,
    eng_scores   : np.ndarray,
    posts        : list,
    alpha: float = 0.40,   # bobot TF-IDF
    beta : float = 0.45,   # bobot BM25
    gamma: float = 0.15,   # bobot engagement
) -> np.ndarray:
    """
    Gabungkan skor TF-IDF, BM25, dan engagement:
      final_score = α·tfidf + β·bm25 + γ·engagement
    
    Bobot: BM25 sedikit lebih tinggi karena lebih robust
    untuk dokumen pendek seperti caption Instagram.
    """
    # Normalisasi engagement ke [0, 1]
    eng_max = eng_scores.max()
    if eng_max > 0:
        eng_norm = eng_scores / eng_max
    else:
        eng_norm = eng_scores

    combined = (alpha * tfidf_scores) + (beta * bm25_scores) + (gamma * eng_norm)
    return combined


def aggregate_by_student(posts: list, combined_scores: np.ndarray) -> list:
    """
    Agregasi skor per NAMA SISWA.
    Jika satu siswa muncul di beberapa post, ambil skor tertinggi
    dan hitung rata-rata skor semua post mereka.
    """
    student_map = defaultdict(list)

    for i, post in enumerate(posts):
        name = post.get("ner_primary_name")
        if not name:
            continue

        student_map[name].append({
            "post_id"        : post.get("id"),
            "url"            : post.get("url"),
            "sekolah"        : post.get("ner_school") or post.get("sekolah"),
            "provinsi"       : post.get("provinsi"),
            "bidang"         : post.get("bidang"),
            "juara"          : post.get("juara"),
            "tingkat"        : post.get("tingkat") or post.get("signals", {}).get("tingkat"),
            "tfidf_score"    : float(tfidf_scores[i]),
            "bm25_score"     : float(bm25_scores[i]),
            "combined_score" : float(combined_scores[i]),
            "likes"          : post.get("likesCount", 0),
            "timestamp"      : post.get("timestamp"),
            "caption_snippet": post.get("caption", "")[:150],
        })

    # Agregasi
    students = []
    for name, records in student_map.items():
        max_record    = max(records, key=lambda r: r["combined_score"])
        avg_combined  = sum(r["combined_score"] for r in records) / len(records)
        max_combined  = max(r["combined_score"] for r in records)

        # Tentukan sekolah (mode dari semua records)
        schools  = [r["sekolah"] for r in records if r["sekolah"]]
        school   = max(set(schools), key=schools.count) if schools else None
        tingkats = [r["tingkat"] for r in records if r["tingkat"]]
        tingkat  = max(set(tingkats), key=tingkats.count) if tingkats else None

        students.append({
            "nama_siswa"          : name,
            "sekolah"             : school,
            "provinsi"            : max_record.get("provinsi"),
            "bidang"              : max_record.get("bidang"),
            "prestasi"            : max_record.get("juara"),
            "tingkat_kompetisi"   : tingkat,
            "cosine_similarity"   : round(max_combined, 6),
            "avg_similarity"      : round(avg_combined, 6),
            "tfidf_score"         : round(max_record["tfidf_score"], 6),
            "bm25_score"          : round(max_record["bm25_score"], 6),
            "jumlah_post"         : len(records),
            "total_likes"         : sum(r["likes"] for r in records),
            "best_post_url"       : max_record["url"],
            "best_post_snippet"   : max_record["caption_snippet"],
            "all_posts"           : records,
        })

    return sorted(students, key=lambda s: s["cosine_similarity"], reverse=True)


def main():
    global tfidf_scores, bm25_scores  # untuk akses di combine_scores
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)
    print(Fore.BLUE + Style.BRIGHT + "  STEP 4: INDEXING TF-IDF & BM25")
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("posts_with_name", data.get("posts", []))
    print(Fore.CYAN + f"[STEP 4] Mengindeks {len(posts):,} post...")

    if not posts:
        print(Fore.RED + "[ERROR] Tidak ada post untuk diindeks!")
        return

    # ─── Build corpus ────────────────────────────────────────────
    corpus_texts, corpus_ids = build_corpus(posts)
    tokenized_corpus = [text.split() for text in corpus_texts]
    query_tokens     = SCHOLARSHIP_QUERY.split()

    print(Fore.CYAN + f"\n  Corpus size     : {len(corpus_texts):,} dokumen")
    print(Fore.CYAN + f"  Query           : '{SCHOLARSHIP_QUERY[:60]}...'")

    # ─── TF-IDF ──────────────────────────────────────────────────
    tfidf_scores, vectorizer = compute_tfidf(corpus_texts, SCHOLARSHIP_QUERY)

    # ─── BM25 ────────────────────────────────────────────────────
    bm25_scores = compute_bm25(tokenized_corpus, query_tokens)

    # ─── Engagement ──────────────────────────────────────────────
    eng_scores = np.array([compute_engagement_score(p) for p in posts])

    # ─── Combined ────────────────────────────────────────────────
    combined = combine_scores(tfidf_scores, bm25_scores, eng_scores, posts)

    # ─── Agregasi per siswa ───────────────────────────────────────
    print(Fore.CYAN + "\n  Mengagregasi skor per siswa...")
    ranked_students = aggregate_by_student(posts, combined)

    print(Fore.GREEN + f"\n  ✔ Total siswa teridentifikasi : {len(ranked_students):,}")
    print(Fore.GREEN + f"  ✔ Top 5 siswa berprestasi:")
    for i, s in enumerate(ranked_students[:5]):
        print(f"    {i+1}. {s['nama_siswa']:<30} | Cosine: {s['cosine_similarity']:.4f} | {s['sekolah'] or '-'}")

    # Tambahkan scores ke post level
    for i, post in enumerate(posts):
        post["_tfidf_score"]    = float(tfidf_scores[i])
        post["_bm25_score"]     = float(bm25_scores[i])
        post["_combined_score"] = float(combined[i])

    output = {
        "summary": {
            **data.get("summary", {}),
            "total_indexed_posts": len(posts),
            "total_students"     : len(ranked_students),
            "query"              : SCHOLARSHIP_QUERY,
            "indexing_weights"   : {"tfidf": 0.40, "bm25": 0.45, "engagement": 0.15},
        },
        "ranked_students": ranked_students,
        "posts_scored"   : posts,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(Fore.GREEN + f"\n  ✔ Output disimpan ke: {OUTPUT_PATH}")
    print(Fore.GREEN + "  ✔ STEP 4 SELESAI\n")
    return ranked_students


if __name__ == "__main__":
    main()
