# Tugas Final — Information Retrieval
## Sistem Pencarian Siswa SMA Berprestasi dari Instagram

> **Mata Kuliah:** Information Retrieval  
> **Topik:** Identifikasi Siswa SMA Berprestasi untuk Program Beasiswa  
> **Data:** Instagram Hashtag Crawling via Apify  
> **Metode:** NER + TF-IDF + BM25 + Cosine Similarity  

---

## 🎯 Tujuan

Membangun sistem Information Retrieval yang dapat:
1. **Crawling** data mentah Instagram menggunakan Apify (hashtag: `#osn2026`, `#siswaprestasi`, dll.)
2. **Preprocessing** teks caption Instagram (cleaning, tokenisasi, stopword removal)
3. **NER** — mengekstrak nama siswa dari caption menggunakan rule-based NER bahasa Indonesia
4. **Indexing** — membangun indeks TF-IDF dan BM25 dari korpus caption
5. **Ranking** — menghitung Cosine Similarity setiap dokumen terhadap query beasiswa
6. **Output** — menghasilkan daftar siswa berprestasi yang diurutkan berdasarkan skor relevansi

---

## 📂 Struktur Folder

```
Tugas Final/
├── main.py                        # Orchestrator (jalankan semua step)
├── quick_run.py                   # Run cepat dari data yang sudah ada
├── requirements.txt               # Python dependencies
├── README.md                      # Dokumentasi ini
│
├── pipeline/                      # Script per tahap pipeline
│   ├── step1_load_raw.py          # Step 1: Load & validasi JSON Apify
│   ├── step2_preprocessing.py     # Step 2: Preprocessing & cleaning teks
│   ├── step3_ner_extraction.py    # Step 3: NER ekstraksi nama siswa
│   ├── step4_indexing_tfidf_bm25.py  # Step 4: TF-IDF + BM25 indexing
│   └── step5_scoring_export.py    # Step 5: Final scoring & export
│
├── data/
│   ├── raw/
│   │   └── raw_posts_apify.json   # Data mentah dari Apify
│   ├── processed/
│   │   ├── data_preprocessed.json # Data sudah diproses (dari Tugas 1)
│   │   ├── step1_loaded.json      # Output Step 1
│   │   ├── step2_cleaned.json     # Output Step 2
│   │   ├── step3_ner.json         # Output Step 3 (dengan nama siswa)
│   │   └── step4_indexed.json     # Output Step 4 (dengan skor)
│   └── output/
│       ├── hasil_siswa_berprestasi.json  # Hasil lengkap JSON
│       ├── hasil_siswa_berprestasi.csv   # Hasil CSV semua siswa
│       └── top100_siswa_beasiswa.csv     # Top 100 kandidat beasiswa
│
└── docs/
    └── pipeline_flow.md           # Dokumentasi alur pipeline
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
cd "Tugas Final"
pip install -r requirements.txt
```

### 2. Jalankan Pipeline Cepat (dari data yang sudah ada)
```bash
python quick_run.py
```

### 3. Jalankan Pipeline Lengkap (dari raw Apify JSON)
```bash
python main.py
```

### 4. Jalankan Hanya Step Tertentu
```bash
python main.py --step 4    # Hanya step 4 (indexing)
python main.py --from 3    # Mulai dari step 3
```

---

## 🔬 Metode & Referensi

### NER (Named Entity Recognition)
- **Pendekatan:** Rule-based NER berbasis pola Bahasa Indonesia
- **Pola:** "selamat kepada [NAMA]", "ananda [NAMA]", dll.
- **Referensi:** Wilie, B. et al. (2020). IndoNLU. AACL-IJCNLP. *(Scopus Q1)*

### TF-IDF (Term Frequency-Inverse Document Frequency)
```
TF-IDF(t,d) = TF(t,d) × log(N / DF(t))
```
- **Referensi:** Sparck Jones, K. (1972). JDoc. *(Scopus Q1)*
- Implementasi: `sklearn.TfidfVectorizer` (sublinear TF, bigram)

### BM25 (Best Match 25)
```
BM25(t,d) = Σ IDF(t) × [TF(t,d)·(k1+1)] / [TF(t,d) + k1·(1-b+b·|d|/avgdl)]
```
- Parameter: k1=1.5, b=0.75 (default Okapi BM25)
- **Referensi:** Robertson & Zaragoza (2009). FTIR. *(Scopus Q1)*

### Cosine Similarity
```
cos(q, d) = (q · d) / (|q| × |d|)
```
- Digunakan untuk mengukur relevansi query beasiswa vs dokumen

### Final Score
```
Final = cosine_combined × level_weight × frequency_bonus
cosine_combined = 0.40·TF-IDF + 0.45·BM25 + 0.15·engagement
level_weight = {Internasional: 1.0, Nasional: 0.85, Provinsi: 0.65, ...}
frequency_bonus = 1.0 + min(0.2, 0.05×(n_posts-1))
```

---

## 📊 Output

| Field | Deskripsi |
|---|---|
| `Nama Siswa` | Nama siswa hasil NER |
| `Sekolah` | SMA/SMK/MA asal siswa |
| `Bidang` | Bidang prestasi (OSN, Olahraga, Seni, dll.) |
| `Tingkat` | Tingkat kompetisi (Nasional, Provinsi, dll.) |
| `Cosine Similarity` | Skor relevansi TF-IDF+BM25 vs query |
| `TF-IDF Score` | Skor TF-IDF murni |
| `BM25 Score` | Skor BM25 murni |
| `Final Score` | Skor akhir dengan bobot level kompetisi |
| `Rekomendasi` | Kategori: SANGAT DIREKOMENDASIKAN / DIREKOMENDASIKAN / dst. |

---

## 📚 Referensi Akademik (Q1 Scopus)

1. Sparck Jones, K. (1972). *A statistical interpretation of term specificity and its application in retrieval.* Journal of Documentation, 28(1), 11-21. **DOI: 10.1108/eb026526**

2. Robertson, S. E. & Zaragoza, H. (2009). *The Probabilistic Relevance Framework: BM25 and Beyond.* Foundations and Trends in Information Retrieval, 3(4), 333-389. **DOI: 10.1561/1500000019**

3. Wilie, B., Vincentio, K., Winata, G. I., et al. (2020). *IndoNLU: Benchmark and Resources for Evaluating Indonesian NLP.* AACL-IJCNLP 2020. **Scopus indexed**

4. Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval.* Cambridge University Press.

5. Nadeau, D. & Sekine, S. (2007). *A survey of named entity recognition and classification.* Lingvisticae Investigationes, 30(1), 3-26. **Scopus Q1**

6. Mikolov, T., et al. (2013). *Distributed Representations of Words and Phrases and their Compositionality.* NeurIPS. **DOI: 10.5555/2999792.2999959**
