"""
=============================================================
STEP 2 - PREPROCESSING & CLEANING TEKS
=============================================================
Referensi:
  - Manning, C. D. et al. (2008). Introduction to Information
    Retrieval. Cambridge University Press. Ch. 2.
  - Haddi, E., Liu, X., & Shi, Y. (2013). The role of text 
    pre-processing in sentiment analysis. Procedia Computer Science.
  - Tala, F. Z. (2003). A Study of Stemming Effects on Information
    Retrieval in Bahasa Indonesia. MIS, UvA.
=============================================================
"""

import json
import re
import string
import unicodedata
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH  = BASE_DIR / "data" / "processed" / "step1_loaded.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "step2_cleaned.json"

# ─── Stopwords Bahasa Indonesia (subset relevan) ──────────────────────────────
STOPWORDS_ID = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
    "pada", "adalah", "atau", "dalam", "tidak", "juga", "sudah", "saya",
    "kita", "kami", "mereka", "akan", "bisa", "ada", "oleh", "atas",
    "sebagai", "telah", "dapat", "nya", "lah", "pun", "lebih", "sangat",
    "serta", "setelah", "sebelum", "agar", "karena", "namun", "tetapi",
    "jika", "ketika", "hingga", "antara", "setiap", "semua", "para",
    "maka", "sedang", "atas", "bagi", "demi", "tanpa", "jauh", "lagi",
    "belum", "pernah", "harus", "perlu", "besar", "kecil", "baru",
    "masih", "sudah", "selalu", "hanya", "saja", "terus", "hal",
    "ya", "yg", "dgn", "dr", "utk", "krn", "tdk", "jd", "bisa",
    "klo", "aja", "nih", "deh", "dong", "banget", "lho", "sih",
}

# ─── Kata kunci prestasi (kata POSITIF yang TIDAK dihapus) ───────────────────
ACHIEVEMENT_KEYWORDS = {
    "juara", "prestasi", "medali", "emas", "perak", "perunggu", "juara1",
    "juara2", "juara3", "olimpiade", "osn", "o2sn", "fls2n", "fls3n",
    "beasiswa", "berprestasi", "nasional", "internasional", "provinsi",
    "kabupaten", "kota", "harapan", "terbaik", "unggul", "lolos", "meraih",
    "berhasil", "pemenang", "nominasi", "finalis", "kompetisi", "lomba",
    "kejuaraan", "piala", "trophy", "penghargaan", "apresiasi",
}


def remove_emoji(text: str) -> str:
    """Hapus emoji dan karakter unicode non-standar."""
    text = unicodedata.normalize("NFKD", text)
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"
        u"\u3030"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(" ", text)


def clean_text(text: str) -> str:
    """
    Membersihkan teks caption Instagram:
    1. Hapus URL
    2. Hapus hashtag symbol (tapi simpan teks)
    3. Hapus mention (@)
    4. Hapus emoji
    5. Normalisasi whitespace
    6. Lowercase
    """
    if not text:
        return ""

    # Hapus URL
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # Hapus mention
    text = re.sub(r"@\w+", " ", text)

    # Hapus hashtag symbol tapi pertahankan teks
    text = re.sub(r"#(\w+)", r"\1", text)

    # Hapus emoji
    text = remove_emoji(text)

    # Hapus karakter non-alfanumerik kecuali spasi
    text = re.sub(r"[^\w\s]", " ", text)

    # Normalisasi whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Lowercase
    text = text.lower()

    return text


def tokenize(text: str) -> list:
    """Tokenisasi sederhana berbasis spasi (tanpa stemming bawaan)."""
    return text.split()


def remove_stopwords(tokens: list) -> list:
    """
    Hapus stopwords, tapi PERTAHANKAN kata kunci prestasi
    (ACHIEVEMENT_KEYWORDS tidak dihapus walau ada di stoplist).
    """
    return [
        t for t in tokens
        if t not in STOPWORDS_ID or t in ACHIEVEMENT_KEYWORDS
    ]


def extract_achievement_signals(text: str, caption_raw: str) -> dict:
    """
    Ekstrak sinyal prestasi dari caption.
    Mendeteksi apakah post membicarakan:
    - Penghargaan/juara
    - Tingkat kompetisi
    - Nama lomba
    - Kelas/jenjang SMA
    """
    text_low = caption_raw.lower()

    # Deteksi kata juara + angka
    juara_pattern = re.search(
        r"juara\s*(1|2|3|i{1,3}|pertama|kedua|ketiga|harapan\s*\d?)", text_low
    )

    # Tingkat kompetisi
    tingkat = None
    if any(w in text_low for w in ["internasional", "international"]):
        tingkat = "Internasional"
    elif any(w in text_low for w in ["nasional", "national"]):
        tingkat = "Nasional"
    elif any(w in text_low for w in ["provinsi", "provincial"]):
        tingkat = "Provinsi"
    elif any(w in text_low for w in ["kabupaten", "kota", "kab."]):
        tingkat = "Kota/Kabupaten"
    elif any(w in text_low for w in ["kecamatan", "sekolah"]):
        tingkat = "Sekolah/Kecamatan"

    # Deteksi SMA/kelas
    is_sma = bool(re.search(r"\b(sma|sman|smk|ma\b|madrasah aliyah)\b", text_low))
    is_kelas_xi = bool(re.search(r"\b(kelas\s*xi|kelas\s*11|xi\s*[a-z]|11\s*[a-z])\b", text_low))

    # Nama lomba
    lomba_types = []
    if re.search(r"\bosn\b", text_low): lomba_types.append("OSN")
    if re.search(r"\bo2sn\b", text_low): lomba_types.append("O2SN")
    if re.search(r"\bfls[23]?n\b", text_low): lomba_types.append("FLS2N/FLS3N")
    if re.search(r"\bopsi\b", text_low): lomba_types.append("OPSI")
    if re.search(r"\bdebat\b", text_low): lomba_types.append("Debat")

    return {
        "juara_detected": juara_pattern.group(0).strip() if juara_pattern else None,
        "tingkat": tingkat,
        "is_sma": is_sma,
        "is_kelas_xi": is_kelas_xi,
        "lomba_types": lomba_types,
        "has_achievement": bool(juara_pattern or tingkat),
    }


def preprocess_post(post: dict) -> dict:
    """Preprocessing lengkap satu post Instagram."""
    caption_raw = post.get("caption", "") or ""

    # Cleaning
    caption_clean = clean_text(caption_raw)

    # Tokenisasi
    tokens_raw = tokenize(caption_clean)

    # Stopword removal
    tokens_filtered = remove_stopwords(tokens_raw)

    # Ekstrak sinyal prestasi
    signals = extract_achievement_signals(caption_clean, caption_raw)

    return {
        **post,
        "caption_clean"    : caption_clean,
        "tokens"           : tokens_filtered,
        "token_count"      : len(tokens_filtered),
        "signals"          : signals,
    }


def main():
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)
    print(Fore.BLUE + Style.BRIGHT + "  STEP 2: PREPROCESSING & TEXT CLEANING")
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)

    # Load
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data["posts"]
    print(Fore.CYAN + f"[STEP 2] Memproses {len(posts):,} post...")

    # Preprocess semua post
    processed = []
    has_achievement = 0
    is_sma_count = 0

    for i, post in enumerate(posts):
        pp = preprocess_post(post)
        processed.append(pp)

        if pp["signals"]["has_achievement"]:
            has_achievement += 1
        if pp["signals"]["is_sma"]:
            is_sma_count += 1

        if (i + 1) % 500 == 0:
            print(Fore.YELLOW + f"  → Diproses: {i+1:,}/{len(posts):,}")

    # Filter hanya post relevan (ada sinyal prestasi)
    relevant = [p for p in processed if p["signals"]["has_achievement"]]

    print(Fore.GREEN + f"\n  ✔ Total diproses          : {len(processed):,}")
    print(Fore.GREEN + f"  ✔ Post dengan prestasi    : {has_achievement:,}")
    print(Fore.GREEN + f"  ✔ Post terkait SMA        : {is_sma_count:,}")
    print(Fore.GREEN + f"  ✔ Post relevan (filter)   : {len(relevant):,}")

    # Simpan hasil
    output = {
        "summary": {
            **data["summary"],
            "total_after_preprocessing": len(processed),
            "total_relevant"           : len(relevant),
            "total_sma"                : is_sma_count,
        },
        "posts_all"     : processed,
        "posts_relevant": relevant,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(Fore.GREEN + f"\n  ✔ Output disimpan ke: {OUTPUT_PATH}")
    print(Fore.GREEN + "  ✔ STEP 2 SELESAI\n")
    return processed, relevant


if __name__ == "__main__":
    main()
