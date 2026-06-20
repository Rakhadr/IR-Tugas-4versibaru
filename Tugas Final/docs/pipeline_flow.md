# Alur Pipeline Information Retrieval
## Pencarian Siswa SMA Berprestasi dari Data Instagram

---

## 📊 Diagram Alur Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INFORMATION RETRIEVAL PIPELINE                        │
│            Pencarian Siswa SMA Berprestasi → Kandidat Beasiswa          │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐
  │   FASE 1: DATA   │
  │   COLLECTION     │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────┐
  │  APIFY Instagram Hashtag Crawler                     │
  │  ─────────────────────────────────────────────────   │
  │  Hashtag yang di-crawl:                              │
  │  • #osn2026      • #siswaberprestasi                 │
  │  • #o2sn2026     • #pelajarberprestasi               │
  │  • #fls2n2026    • #prestasisiswa                    │
  │  • #fls3n2026    • #medaliosn                        │
  │  • #osn2025      • #juaranasional                    │
  │                                                      │
  │  Output: raw_posts_apify.json (~1,025 post)          │
  │  Field: id, caption, ownerFullName, hashtags,        │
  │         likesCount, timestamp, locationName, ...     │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌──────────────────┐
  │   FASE 2: PRE-   │
  │   PROCESSING     │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────┐
  │  STEP 2: Text Preprocessing                          │
  │  ─────────────────────────────────────────────────   │
  │  1. Hapus URL, mention (@), emoji                    │
  │  2. Normalize hashtag (#osn → osn)                   │
  │  3. Lowercase                                        │
  │  4. Tokenisasi (split by whitespace)                 │
  │  5. Stopword Removal (Bahasa Indonesia)              │
  │  6. Ekstrak sinyal prestasi (juara, tingkat, dll.)   │
  │                                                      │
  │  Referensi: Manning et al. (2008). IIR. Ch.2         │
  │  Output: tokens[], caption_clean, signals{}          │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌──────────────────┐
  │   FASE 3: NER    │
  │   EXTRACTION     │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────┐
  │  STEP 3: Named Entity Recognition (NER)              │
  │  ─────────────────────────────────────────────────   │
  │  Strategi 1 — Rule-Based NER (Presisi Tinggi):       │
  │    • Pattern: "selamat kepada [NAMA]"                │
  │    • Pattern: "ananda [NAMA]"                        │
  │    • Pattern: "sukses untuk [NAMA]"                  │
  │    • Pattern: "juara X: [NAMA]"                      │
  │                                                      │
  │  Strategi 2 — Heuristic NER (Recall Tinggi):         │
  │    • Pola kapitalisasi nama Indonesia                 │
  │    • Minimal 2 kata, tidak ada kata blacklist         │
  │                                                      │
  │  Validasi:                                           │
  │    • 2-5 kata, panjang 4-50 karakter                 │
  │    • Tidak mengandung angka atau kata umum            │
  │                                                      │
  │  Referensi: Wilie et al. (2020). IndoNLU. Scopus Q1  │
  │  Output: ner_primary_name, ner_confidence{HIGH/LOW}  │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌──────────────────┐
  │   FASE 4:        │
  │   INDEXING       │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────┐
  │  STEP 4A: TF-IDF Indexing                            │
  │  ─────────────────────────────────────────────────   │
  │                                                      │
  │  TF(t,d)  = count(t in d) / total_terms(d)          │
  │  IDF(t)   = log((1 + N) / (1 + DF(t))) + 1          │
  │  TFIDF    = TF × IDF  (sublinear_tf=True)            │
  │                                                      │
  │  Vectorizer: sklearn.TfidfVectorizer                 │
  │    - ngram_range: (1,2)  → unigram + bigram          │
  │    - min_df=1, max_df=0.95                           │
  │    - sublinear_tf=True (log normalization)           │
  │                                                      │
  │  Query → TF-IDF vector                               │
  │  Cosine(q, d) = dot(q,d) / (|q|×|d|)               │
  │                                                      │
  │  Ref: Sparck Jones (1972). JDoc. Scopus Q1           │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌─────────────────────────────────────────────────────┐
  │  STEP 4B: BM25 Okapi Indexing                        │
  │  ─────────────────────────────────────────────────   │
  │                                                      │
  │  BM25(t,d) = IDF(t) ×                               │
  │    [TF(t,d)·(k1+1)] / [TF(t,d)+k1·(1-b+b·|d|/avgdl)]│
  │                                                      │
  │  Parameter: k1=1.5, b=0.75                           │
  │  Library: rank_bm25.BM25Okapi                        │
  │                                                      │
  │  BM25 cocok untuk dokumen pendek (caption Instagram) │
  │  karena normalisasi panjang dokumen lebih baik       │
  │                                                      │
  │  Ref: Robertson & Zaragoza (2009). FTIR. Scopus Q1   │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌─────────────────────────────────────────────────────┐
  │  STEP 4C: Engagement Score                           │
  │  ─────────────────────────────────────────────────   │
  │                                                      │
  │  Engagement = log(1 + likes + 2×comments)            │
  │  Dinormalisasi ke [0,1]                              │
  │                                                      │
  │  Alasan: Post dengan engagement tinggi = lebih valid  │
  │  dan lebih mungkin berisi informasi prestasi nyata   │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌─────────────────────────────────────────────────────┐
  │  STEP 4D: Combined Cosine Similarity                 │
  │  ─────────────────────────────────────────────────   │
  │                                                      │
  │  combined = 0.40·TF-IDF + 0.45·BM25 + 0.15·Engagement│
  │                                                      │
  │  Bobot BM25 > TF-IDF karena lebih robust untuk       │
  │  teks pendek (rata-rata 100-200 kata per caption)    │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌──────────────────┐
  │   FASE 5:        │
  │   RANKING        │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────┐
  │  STEP 5: Final Scoring & Ranking                     │
  │  ─────────────────────────────────────────────────   │
  │                                                      │
  │  Agregasi per Nama Siswa:                            │
  │    • Ambil skor tertinggi dari semua post siswa      │
  │    • Hitung frequency bonus (posting ulang = lebih   │
  │      dapat dipercaya)                                │
  │                                                      │
  │  Level Weight (bobot tingkat kompetisi):             │
  │    • Internasional  : 1.00                           │
  │    • Nasional       : 0.85                           │
  │    • Provinsi       : 0.65                           │
  │    • Kota/Kabupaten : 0.45                           │
  │    • Sekolah        : 0.25                           │
  │                                                      │
  │  Final Score = cosine × level_weight × freq_bonus    │
  │                                                      │
  │  Klasifikasi Rekomendasi:                            │
  │    ≥ 0.20 → SANGAT DIREKOMENDASIKAN                 │
  │    ≥ 0.10 → DIREKOMENDASIKAN                        │
  │    ≥ 0.05 → PERTIMBANGKAN                           │
  │    < 0.05 → PERLU VERIFIKASI                        │
  └─────────────────────┬───────────────────────────────┘
                        │
                        ▼
  ┌──────────────────┐
  │   OUTPUT AKHIR   │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────┐
  │  HASIL AKHIR                                         │
  │  ─────────────────────────────────────────────────   │
  │                                                      │
  │  Kolom Output:                                       │
  │  ┌──────────────────────────────────────────────┐   │
  │  │ Rank │ Nama Siswa │ Sekolah │ Bidang          │   │
  │  │ Cosine Similarity │ TF-IDF │ BM25            │   │
  │  │ Final Score │ Rekomendasi │ URL Post          │   │
  │  └──────────────────────────────────────────────┘   │
  │                                                      │
  │  File Output:                                        │
  │  • hasil_siswa_berprestasi.json (semua data)         │
  │  • hasil_siswa_berprestasi.csv  (tabel lengkap)      │
  │  • top100_siswa_beasiswa.csv    (top 100)            │
  └─────────────────────────────────────────────────────┘
```

---

## 🔑 Komponen Kunci

### Query Pencarian (Beasiswa)
```
"siswa berprestasi juara olimpiade sains nasional osn beasiswa sma 
medali emas perak prestasi akademik terbaik kompetisi unggul 
juara pertama kedua ketiga lomba nasional internasional 
kelas xi sma sman smk madrasah aliyah"
```

### Bobot Skor Akhir
| Komponen | Bobot | Alasan |
|---|---|---|
| BM25 | 45% | Lebih robust untuk teks pendek |
| TF-IDF | 40% | Standard IR weighting |
| Engagement | 15% | Validasi sosial post |

---

## 📚 Referensi Utama

| Referensi | Kontribusi | Index |
|---|---|---|
| Sparck Jones (1972) | Dasar TF-IDF | Scopus Q1 |
| Robertson & Zaragoza (2009) | BM25 framework | Scopus Q1 |
| Manning et al. (2008) | IIR textbook | Standard |
| Wilie et al. (2020) | IndoNLU/NER Bahasa Indonesia | Scopus Q1 |
| Nadeau & Sekine (2007) | Survey NER | Scopus Q1 |
| Wahyudi et al. (2019) | TF-IDF beasiswa | Scopus indexed |
