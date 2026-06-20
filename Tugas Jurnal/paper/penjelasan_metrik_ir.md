# Penjelasan Metrik Evaluasi Information Retrieval (IR)

Dokumen ini menjelaskan secara rinci metrik-metrik yang digunakan dalam evaluasi sistem *Information Retrieval* (IR) pada pencarian siswa berprestasi, serta pengaruh dan interpretasinya terhadap perbandingan antara pendekatan *Lexical* (TF-IDF + BM25) dan *Semantic* (LLM Pretrained).

---

## 1. Ground Truth Relevan
**Definisi:** *Ground Truth* adalah data pelabelan manual atau semi-otomatis yang dianggap sebagai kebenaran mutlak (standar emas) untuk menguji keakuratan algoritma. Dalam konteks sistem kita, kandidat dinilai relevan (nilai 1) jika memenuhi syarat: namanya valid (bukan frasa *noise* NER), jenjang pendidikannya SMA/SMK/MA, dan terdapat bukti prestasi nyata di teks *caption*. Jika kandidat adalah jenjang SD/SMP, universitas, atau sekadar ekstrak kata yang salah (misalnya "dalam menimba ilmu"), maka dinilai tidak relevan (nilai 0).

**Pengaruhnya:** *Ground Truth* adalah pondasi seluruh metrik. Tanpa *ground truth* yang valid, mustahil mengukur seberapa baik sistem membedakan informasi yang benar-benar dicari (*signal*) dari informasi acak yang terbawa (*noise*).

---

## 2. Precision@K (Misal: Precision@10)
**Definisi:** *Precision@K* (Presisi pada Peringkat ke-K) mengukur persentase atau proporsi dokumen relevan yang berada pada urutan K teratas dari hasil pencarian.
**Rumus:** `Jumlah dokumen relevan di top K / K`

**Pengaruh dalam Eksperimen:**
- **Pada K=5 (Sangat Sempit):** Lexical IR mencapai Precision 1.0 (sempurna), artinya 5 orang teratas hasil TF-IDF semuanya relevan. Lexical menang karena kata kunci kueri yang sangat persis (seperti "olimpiade sains nasional") akan mengangkat dokumen relevan ke posisi paling atas. Semantic LLM mungkin menampilkan *noise* NER di posisi atas karena ada kesamaan konteks kalimat secara umum (Precision 0.8).
- **Pada K=10 atau lebih:** Precision@10 untuk LLM adalah 0.8, lebih baik dibanding Lexical yang turun menjadi 0.7. Ini berarti ketika kita mencari lebih banyak kandidat, LLM lebih stabil memberikan rekomendasi relevan karena ia paham konteks (misal frasa "juara umum 3 silat" tetap dideteksi relevan meskipun kuerinya "juara olimpiade sains"), sedangkan metode Lexical kehabisan dokumen yang kata kuncinya persis sama.

---

## 3. Recall@K
**Definisi:** *Recall@K* mengukur persentase dokumen relevan yang berhasil ditemukan di top K, dibandingkan dengan **keseluruhan** dokumen relevan yang ada di *ground truth*.
**Rumus:** `Jumlah dokumen relevan di top K / Total dokumen relevan di Ground Truth`

**Pengaruh dalam Eksperimen:**
LLM memiliki *Recall@50* yang lebih tinggi (0.5405) dibanding Lexical (0.5000). Ini menunjukkan LLM lebih sukses dalam "menemukan siswa berprestasi yang tersembunyi" (siswa yang tidak menggunakan kata kunci beasiswa/OSN secara eksplisit di profil mereka tetapi konteksnya prestasi).

---

## 4. Lexical MAP dan Semantic MAP (Mean Average Precision)
**Definisi:** *Average Precision* (AP) adalah rata-rata nilai presisi yang dihitung setiap kali sistem menemukan satu dokumen yang relevan. MAP adalah rata-rata dari AP untuk berbagai kueri. Karena kita menggunakan 1 kueri utama, MAP = AP. Metrik ini mengukur kualitas peringkat secara agregat: jika sistem meletakkan dokumen relevan di peringkat bawah, MAP-nya akan turun drastis.

**Pengaruh dalam Eksperimen:**
- **Lexical MAP (0.7653):** Sudah sangat baik karena TF-IDF mengangkat dokumen yang 100% *exact match* ke urutan teratas, sehingga akumulasi presisi di peringkat atas sangat padat.
- **Semantic MAP (0.7729):** Sedikit lebih unggul (+0.0076) karena LLM menjaga kerapatan dokumen relevan bahkan hingga peringkat tengah dan bawah, memberikan prioritas yang stabil berdasarkan makna ketimbang *keyword*.

---

## 5. NDCG@K (Normalized Discounted Cumulative Gain)
**Definisi:** NDCG sangat mengutamakan urutan posisi. Berbeda dengan *Precision* yang menganggap peringkat 1 dan peringkat 10 sama-sama bernilai 1 "relevan", NDCG memberikan penalti logaritmik (diskon) pada dokumen relevan yang berada di peringkat bawah. Dokumen relevan di urutan #1 jauh lebih berharga dari urutan #5.

**Pengaruh dalam Eksperimen:**
- **NDCG@5:** Lexical unggul sempurna (1.0000) karena peringkat 1-5 semuanya relevan secara mutlak.
- **NDCG@50:** Semantic LLM sedikit lebih baik (0.7645 vs 0.7630). Ini memvalidasi bahwa dalam daftar panjang (50 kandidat), urutan prioritas yang dihasilkan LLM lebih berkualitas secara holistik ketimbang Lexical.

---

## 6. Spearman's Rank Correlation (Korelasi Peringkat Spearman)
**Definisi:** Mengukur arah dan kekuatan hubungan berurutan antara dua pemeringkatan (ranking yang dihasilkan metode Lexical vs metode Semantic). Nilainya berkisar dari -1 (berlawanan total) hingga +1 (urutan peringkat sama persis). 

**Pengaruh dalam Eksperimen:**
Nilai $\rho$ = 0.5043 ($p \ll 0.05$) menunjukkan korelasi positif tingkat **sedang-kuat**. Artinya, siswa yang dinilai berprestasi tinggi oleh Lexical secara umum juga dinilai berprestasi tinggi oleh LLM. Namun, karena tidak mencapai 0.9 atau 1.0, terjadi fenomena **Rank Drift** (pergeseran peringkat yang signifikan) akibat perbedaan mendasar paradigma pencarian kata kunci eksak vs pemahaman konteks.

---

## 7. Kendall's Tau Correlation
**Definisi:** Mirip dengan Spearman, namun Kendall's Tau mengukur korelasi berdasarkan *concordant pairs* dan *discordant pairs* (pasangan item yang urutannya searah vs berlawanan). Kendall lebih tangguh (*robust*) terhadap dataset dengan banyak *ties* (skor yang sama) atau distribusi tidak normal.

**Pengaruh dalam Eksperimen:**
Nilai $\tau$ = 0.3499. Secara statistik, nilai Kendall memang selalu lebih rendah daripada Spearman. Ini mengonfirmasi konsistensi temuan Spearman bahwa ada keselarasan arah yang kuat namun memiliki perbedaan prioritas pasangan (*discordance*) yang lumayan tinggi antara LLM dan Baseline.

---

## 8. Pearson Score Correlation
**Definisi:** Berbeda dengan Spearman dan Kendall yang hanya mengukur "urutan peringkat" (1, 2, 3), Pearson mengukur korelasi linier dari **nilai skor aktual** (misal skor 0.1716 vs 0.2070). 

**Pengaruh dalam Eksperimen:**
Nilai $r$ = 0.5215. Membuktikan bahwa fungsi distribusi pembobotan (*scoring distribution*) antara Baseline dan LLM tidak saling bertabrakan, tetapi memiliki skala *variance* yang bervariasi. Hal ini mendukung rekomendasi untuk metode *Hybrid Search* (menggabungkan kedua metode) karena masing-masing algoritma melihat sinyal relevansi dari dimensi yang berbeda.
