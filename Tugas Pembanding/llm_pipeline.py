"""
=============================================================
TUGAS PEMBANDING - LLM PRETRAINED PIPELINE
=============================================================
Menjalankan pencarian siswa berprestasi menggunakan pretrained LLM
(sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) 
berbasis dense embedding similarity.

Referensi:
  - Reimers, N. & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings
    using Siamese BERT-Networks. EMNLP 2019. (Scopus Q1)
  - Devlin, J. et al. (2018). BERT: Pre-training of Deep Bidirectional
    Transformers for Language Understanding. arXiv.
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
from tqdm import tqdm

# Transformers & PyTorch
import torch
from transformers import AutoTokenizer, AutoModel

init(autoreset=True)

# Path definition
BASE_DIR          = Path(__file__).resolve().parent
DATA_INPUT        = BASE_DIR.parent / "Tugas Final" / "data" / "processed" / "data_preprocessed.json"
OUTPUT_DIR        = BASE_DIR / "data" / "output"
OUTPUT_JSON       = OUTPUT_DIR / "hasil_siswa_berprestasi_llm.json"
OUTPUT_CSV        = OUTPUT_DIR / "hasil_siswa_berprestasi_llm.csv"
OUTPUT_TOP100     = OUTPUT_DIR / "top100_siswa_beasiswa_llm.csv"

# Pretrained Model Name
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Query pencarian beasiswa (sama seperti baseline)
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
    """Preprocess text caption untuk matching/embedding."""
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
    """Load data dari data_preprocessed.json."""
    if not DATA_INPUT.exists():
        raise FileNotFoundError(f"Data input tidak ditemukan di: {DATA_INPUT}\nPastikan Tugas Final sudah dijalankan!")
    
    with open(DATA_INPUT, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        rows = raw.get("rows", raw.get("posts", []))
    else:
        rows = []

    print(Fore.CYAN + f"  Data dimuat: {len(rows):,} record")
    return rows

def mean_pooling(model_output, attention_mask):
    """Mean Pooling untuk menghasilkan sentence embedding dari token embeddings."""
    token_embeddings = model_output[0] # First element contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return sum_embeddings / sum_mask

def compute_embeddings(texts: list, model_name: str, batch_size: int = 32) -> np.ndarray:
    """Hitung dense embeddings menggunakan model HuggingFace."""
    print(Fore.CYAN + f"  Loading HuggingFace model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    
    # Set model to evaluation mode
    model.eval()
    
    # Gunakan GPU jika tersedia
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(Fore.CYAN + f"  Running on device: {device}")
    model = model.to(device)

    all_embeddings = []
    
    print(Fore.CYAN + f"  Encoding {len(texts):,} dokumen...")
    for i in tqdm(range(0, len(texts), batch_size), desc="Encoding batches"):
        batch_texts = texts[i:i+batch_size]
        
        # Tokenize
        encoded_input = tokenizer(
            batch_texts, 
            padding=True, 
            truncation=True, 
            max_length=256, 
            return_tensors='pt'
        ).to(device)
        
        # Compute embeddings
        with torch.no_grad():
            model_output = model(**encoded_input)
            
        # Mean Pooling
        batch_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
        
        # Move back to CPU and convert to numpy
        all_embeddings.append(batch_embeddings.cpu().numpy())
        
    return np.vstack(all_embeddings)

def run_llm_pipeline(rows: list) -> list:
    """Pipeline LLM: NLP -> LLM Embedding Similarity -> Aggregation -> Recommendation."""
    # 1. Filter hanya yang punya nama siswa
    with_name = [r for r in rows if r.get("nama_siswa") and len(str(r["nama_siswa"])) > 2]
    print(Fore.CYAN + f"  Record dengan nama_siswa: {len(with_name):,}")

    if not with_name:
        print(Fore.RED + "  [ERROR] Tidak ada record dengan nama siswa untuk diproses!")
        return []

    # 2. Buat corpus dokumen (sama persis dengan cara baseline)
    corpus_clean = []
    for r in with_name:
        text = f"{r.get('caption', '')} {r.get('nama_siswa', '')} {r.get('sekolah', '')} {r.get('bidang', '')} {r.get('juara', '')}"
        corpus_clean.append(clean_text(text))

    query_clean = clean_text(QUERY)

    # 3. Hitung Embeddings
    # Gabungkan corpus + query untuk batching atau encode terpisah
    doc_embeddings = compute_embeddings(corpus_clean, MODEL_NAME)
    query_embedding = compute_embeddings([query_clean], MODEL_NAME)[0]

    # 4. Hitung Cosine Similarity
    print(Fore.CYAN + "  Menghitung LLM Cosine Similarity...")
    # Normalize embeddings untuk cosine similarity (dot product of L2 normalized vectors)
    doc_norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
    doc_norms = np.where(doc_norms == 0, 1e-9, doc_norms) # prevent division by zero
    doc_emb_norm = doc_embeddings / doc_norms

    query_norm = np.linalg.norm(query_embedding)
    query_norm = 1e-9 if query_norm == 0 else query_norm
    query_emb_norm = query_embedding / query_norm

    # Cosine Similarity = dot product
    llm_sim_scores = np.dot(doc_emb_norm, query_emb_norm)
    
    # Skala similarity LLM biasanya di range yang berbeda, normalisasi ke [0, 1] jika ada nilai negatif
    sim_min, sim_max = llm_sim_scores.min(), llm_sim_scores.max()
    print(Fore.GREEN + f"  ✔ LLM Similarity range: [{sim_min:.4f} – {sim_max:.4f}]")
    
    # Simpan raw similarity
    for i, r in enumerate(with_name):
        r["_llm_sim"] = float(llm_sim_scores[i])

    # 5. Engagement score (sama seperti baseline)
    eng_raw = np.array([math.log1p(max(0, r.get("likes", 0) or 0)) for r in with_name])
    eng_max = eng_raw.max()
    eng_scores = eng_raw / eng_max if eng_max > 0 else eng_raw

    # 6. Combined score: 85% LLM embedding similarity + 15% engagement
    # Catatan: Kita ganti bobot TF-IDF + BM25 (85%) dengan LLM similarity (85%)
    combined = (0.85 * llm_sim_scores) + (0.15 * eng_scores)

    for i, r in enumerate(with_name):
        r["_llm_score"] = float(llm_sim_scores[i])
        r["_eng_score"] = float(eng_scores[i])
        r["_combined_score"] = float(combined[i])

    # 7. Agregasi per nama siswa
    from collections import defaultdict
    student_map = defaultdict(list)
    for r in with_name:
        name = str(r["nama_siswa"]).strip()
        student_map[name].append(r)

    students = []
    for name, records in student_map.items():
        best = max(records, key=lambda r: r["_combined_score"])
        tingkat = best.get("tingkat") or best.get("signals", {}).get("tingkat") if isinstance(best.get("signals"), dict) else None
        lw = LEVEL_WEIGHTS.get(tingkat, 0.30)
        n_posts = len(records)
        freq_b = 1.0 + min(0.20, 0.05 * (n_posts - 1))
        
        cosine = best["_combined_score"]
        final = round(cosine * lw * freq_b, 6)

        # Gunakan threshold klasifikasi beasiswa yang sama
        if final >= 0.20:
            reko = "SANGAT DIREKOMENDASIKAN"
        elif final >= 0.10:
            reko = "DIREKOMENDASIKAN"
        elif final >= 0.05:
            reko = "PERTIMBANGKAN"
        else:
            reko = "PERLU VERIFIKASI"

        students.append({
            "nama_siswa"         : name,
            "sekolah"            : best.get("sekolah"),
            "provinsi"           : best.get("provinsi"),
            "bidang"             : best.get("bidang"),
            "prestasi"           : best.get("juara"),
            "tingkat_kompetisi"  : tingkat,
            "cosine_similarity"  : round(cosine, 6),
            "llm_sim_score"      : round(best["_llm_score"], 6),
            "eng_score"          : round(best["_eng_score"], 6),
            "final_score"        : final,
            "rekomendasi"        : reko,
            "jumlah_post"        : n_posts,
            "total_likes"        : sum(r.get("likes", 0) or 0 for r in records),
            "kelas_xi"           : best.get("kelas_xi", False),
            "best_post_url"      : best.get("url"),
            "caption_snippet"    : str(best.get("caption", ""))[:150],
        })

    # Urutkan berdasarkan final_score
    students.sort(key=lambda s: s["final_score"], reverse=True)
    for i, s in enumerate(students):
        s["rank"] = i + 1

    return students

def print_table(students: list, n: int = 30):
    """Print tabel hasil di terminal."""
    print(Fore.BLUE + Style.BRIGHT + "\n" + "═" * 110)
    print(Fore.BLUE + Style.BRIGHT + "  HASIL AKHIR: SISWA SMA BERPRESTASI — LLM PRETRAINED EMBEDDING PIPELINE")
    print(Fore.BLUE + Style.BRIGHT + "═" * 110)
    h = f"{'#':>3}  {'Nama Siswa':<26} {'Sekolah':<22} {'Bidang':<16} {'Tingkat':<12} {'LLM Sim':>7} {'Eng Score':>9} {'Final':>7}  Rekomendasi"
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
            f"{s['llm_sim_score']:>7.4f} "
            f"{s['eng_score']:>9.4f} "
            f"{s['final_score']:>7.4f}  "
            f"{s['rekomendasi']}"
        ))
    print(Fore.WHITE + "─" * 110)

def main():
    print(Fore.BLUE + Style.BRIGHT + """
╔═══════════════════════════════════════════════════════════╗
║   LLM PRETRAINED EMBEDDINGS PIPELINE (MiniLM)             ║
║   Semantic Dense Retrieval & Student Ranking              ║
╚═══════════════════════════════════════════════════════════╝
""")

    print(Fore.CYAN + "[1/4] Loading preprocessed data...")
    rows = load_data()

    print(Fore.CYAN + "\n[2/4] Running LLM Embedding Pipeline...")
    students = run_llm_pipeline(rows)

    if not students:
        print(Fore.RED + "Gagal memproses siswa.")
        return

    print(Fore.CYAN + "\n[3/4] Menampilkan hasil top siswa (LLM)...")
    print_table(students, n=30)

    # Stats
    dist = {}
    for s in students:
        dist[s["rekomendasi"]] = dist.get(s["rekomendasi"], 0) + 1
    print(Fore.CYAN + "\n  Distribusi Rekomendasi (LLM):")
    for k, v in dist.items():
        print(f"    {k:<28}: {v}")

    print(Fore.CYAN + f"\n[4/4] Menyimpan output LLM...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_students": len(students),
                "query": QUERY,
                "metode": f"LLM Pretrained Embedding ({MODEL_NAME})",
                "embedding_model": MODEL_NAME,
                "weights": {"llm_sim": 0.85, "engagement": 0.15},
            },
            "students": students,
        }, f, ensure_ascii=False, indent=2)
    print(Fore.GREEN + f"  ✔ JSON → {OUTPUT_JSON}")

    # CSV Full
    df = pd.DataFrame([{
        "Rank"              : s["rank"],
        "Nama Siswa"        : s["nama_siswa"],
        "Sekolah"           : s["sekolah"],
        "Provinsi"          : s["provinsi"],
        "Bidang"            : s["bidang"],
        "Prestasi"          : s["prestasi"],
        "Tingkat"           : s["tingkat_kompetisi"],
        "Cosine Similarity" : s["cosine_similarity"],
        "LLM Sim Score"     : s["llm_sim_score"],
        "Eng Score"         : s["eng_score"],
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

    print(Fore.GREEN + Style.BRIGHT + "\n  ✔ LLM PIPELINE SELESAI!\n")

if __name__ == "__main__":
    main()
