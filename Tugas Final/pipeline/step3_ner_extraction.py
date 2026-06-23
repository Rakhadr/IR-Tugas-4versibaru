"""
=============================================================
STEP 3 - NER (NAMED ENTITY RECOGNITION) - EKSTRAKSI NAMA SISWA
=============================================================
Referensi:
  - Nadeau, D. & Sekine, S. (2007). A survey of named entity
    recognition and classification. Lingvisticae Investigationes.
  - Wilie, B. et al. (2020). IndoNLU: Benchmark and Resources for
    Evaluating Indonesian NLP. AACL-IJCNLP. (Q1 Scopus)
  - Kurniawan, K. & Louvan, S. (2021). IndoLEM and IndoBERT.
    COLING 2020. (Scopus indexed)
  
Pendekatan:
  1. Rule-based NER (Regex + pola Bahasa Indonesia) → cepat & ringan
  2. Heuristic NER (pola "selamat kepada [NAMA]") → presisi tinggi
  3. Optional: IndoBERT dari HuggingFace (jika tersedia GPU/RAM)
=============================================================
"""

import json
import re
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

BASE_DIR    = Path(__file__).resolve().parent.parent
INPUT_PATH  = BASE_DIR / "data" / "processed" / "step2_cleaned.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "step3_ner.json"

# ─── Pola trigger kalimat penghargaan ─────────────────────────────────────────
CONGRATULATION_PATTERNS = [
    # "selamat kepada NAMA" / "selamat untuk NAMA"
    r"selamat\s+(?:kepada|untuk|bagi|atas\s+prestasi)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})",
    # "apresiasi kepada NAMA"
    r"apresiasi\s+(?:kepada|untuk)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})",
    # "kepada ananda NAMA"
    r"(?:kepada\s+)?ananda\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})",
    # "sukses untuk NAMA"
    r"(?:selamat\s+dan\s+)?sukses\s+(?:kepada|untuk)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})",
    # "atas nama NAMA"
    r"atas\s+nama\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})",
    # "selamat kepada siswa(i) kami NAMA"
    r"siswa(?:i)?\s+(?:kami|hebat|terbaik|berprestasi)(?:\s+\w+){0,3}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})",
    # "kepada saudara/i NAMA"
    r"(?:kepada\s+)?(?:saudara|saudari|kak|kakak)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})",
    # Nama setelah "Juara X:"
    r"juara\s*[123i]{1,4}[^a-zA-Z]{0,10}([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})",
]

# ─── Pola nama Indonesia (heuristic) ──────────────────────────────────────────
# Nama Indonesia umumnya: 2-5 kata, tiap kata diawali huruf kapital
INDONESIAN_NAME_PATTERN = re.compile(
    r"\b([A-Z][a-z]{1,}(?:\s+[A-Z][a-z]{1,}){1,4})\b"
)

# ─── Kata bukan nama (false positives umum) ──────────────────────────────────
BLACKLIST_WORDS = {
    # Ucapan / kata sapaan
    "Selamat", "Sukses", "Semoga", "Alhamdulillah", "Teruslah", "Semangat",
    "Bangga", "Terus", "Terima", "Kasih", "Ananda", "Kepada", "Untuk",
    "Kami", "Kita", "Mereka", "Atas", "Pada",

    # Prestasi / kompetisi
    "Juara", "Olimpiade", "Sains", "Prestasi", "Lomba", "Kompetisi",
    "Festival", "Tingkat", "Bidang", "Nasional", "Internasional", "Provinsi",

    # Mata pelajaran / bidang
    "Matematika", "Biologi", "Fisika", "Kimia", "Informatika", "Geografi",
    "Ekonomi", "Astronomi", "Kebumian", "Bahasa", "Inggris", "Indonesia",
    "Sejarah", "Sosiologi", "Akuntansi", "Sastra", "Komputer",

    # Olahraga / seni
    "Renang", "Futsal", "Pencak", "Silat", "Gaya", "Kupu", "Jurus",
    "Tunggal", "Tari", "Kreasi", "Vokal", "Musik", "Paduan", "Suara",

    # Peran / jabatan
    "Guru", "Pembimbing", "Kepala", "Wakil", "Staff", "Siswa", "Siswi",
    "Murid", "Pelajar", "Mahasiswa", "Dosen", "Pelatih", "Pendamping",
    "Kejuruan", "Umum",

    # Institusi / organisasi
    "Sekolah", "Madrasah", "Islam", "Negeri", "Swasta", "Nahdlatul", "Ulama",
    "Boarding", "School", "Lentera", "Harapan", "Syifa", "Granada",
    "SMA", "SMK", "SMAN", "SMP", "SMPN", "SD", "SDN", "MA", "MAN", "MTs",

    # Kata kerja / frasa aksi
    "Meraih", "Melangkah", "Menuju", "Kick", "Follow", "Registrasi",
    "Dokumentasi", "Simulasi", "Berhasil", "Raih", "Jadwal", "Pelaksanaan",

    # Bahasa Inggris umum
    "Level", "Advanced", "On", "Instagram", "Championship", "Gold", "Silver",
    "Bronze", "Center", "Admin",

    # Kata sifat / keterangan
    "Unggul", "Terbaik", "Hebat", "Luar", "Biasa", "Masa", "Depan",
    "Gratis", "Lebih", "Dekat", "Seluruh", "Fasilitas", "Laboratorium",

    # Penghargaan
    "Emas", "Perak", "Perunggu",

    # Geografi Indonesia
    "Kabupaten", "Kota", "Jawa", "Barat", "Timur", "Tengah", "Sulawesi",
    "Sumatera", "Kalimantan", "Jakarta", "Bandung", "Surabaya", "Yogyakarta",
    "Bali", "Aceh", "Lampung", "Riau", "Jambi", "Bengkulu", "Palembang",
    "Medan", "Makassar", "Manado", "Pontianak", "Samarinda", "Ambon", "Papua",
    "Wonosari", "Amuntai",

    # Hari / bulan
    "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu",
    "Monday", "Tuesday", "January", "February",
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
}


def extract_name_from_congratulation(caption: str) -> list:
    """
    Strategi 1 - Rule-based NER:
    Ekstrak nama dari pola kalimat ucapan selamat/penghargaan.
    Presisi tinggi karena menggunakan konteks linguistik.
    """
    names = []
    for pattern in CONGRATULATION_PATTERNS:
        matches = re.findall(pattern, caption, re.IGNORECASE)
        for m in matches:
            m = m.strip()
            if is_valid_name(m):
                names.append(m)
    return list(set(names))


def extract_name_heuristic(caption: str) -> list:
    """
    Strategi 2 - Heuristic NER:
    Cari pola kapitalisasi nama Indonesia di seluruh teks.
    Lebih banyak noise, tapi meningkatkan recall.
    """
    candidates = INDONESIAN_NAME_PATTERN.findall(caption)
    valid = []
    for name in candidates:
        words = name.split()
        # Minimal 2 kata, tidak ada kata dalam blacklist
        if len(words) >= 2 and is_valid_name(name):
            valid.append(name)
    return list(set(valid))


def is_valid_name(name: str) -> bool:
    """
    Validasi apakah string adalah nama manusia yang valid.
    Kriteria:
    - 2-5 kata
    - Tidak mengandung kata dalam blacklist
    - Tidak mengandung angka atau newline
    - Panjang total 4-50 karakter
    - Setiap kata diawali huruf kapital (bukan lowercase / ALL CAPS panjang)
    """
    if not name or len(name) < 4 or len(name) > 50:
        return False

    # Tolak jika ada newline (artefak gabungan dua kalimat)
    if "\n" in name or "\r" in name:
        return False

    words = name.strip().split()
    if len(words) < 2 or len(words) > 5:
        return False

    if re.search(r"\d", name):
        return False

    for word in words:
        if len(word) < 2:
            return False

        # Setiap kata harus diawali huruf kapital
        if not word[0].isupper():
            return False

        # Tolak kata ALL CAPS lebih dari 3 karakter (bukan inisial/singkatan nama)
        if word.isupper() and len(word) > 3:
            return False

        if word in BLACKLIST_WORDS:
            return False

    return True


def merge_names(rule_names: list, heuristic_names: list) -> tuple:
    """
    Gabungkan hasil dua strategi NER.
    - High confidence: nama dari rule-based
    - Low confidence: nama dari heuristic saja
    Returns: (all_names, confidence_map)
    """
    confidence = {}
    for n in rule_names:
        confidence[n] = "HIGH"
    for n in heuristic_names:
        if n not in confidence:
            confidence[n] = "LOW"

    return list(confidence.keys()), confidence


def extract_school(caption: str):
    """Ekstrak nama sekolah dari caption."""
    patterns = [
        r"(SMA(?:N|K)?\s+(?:Negeri\s+)?\d+\s+\w+)",
        r"(SMA\s+\w+(?:\s+\w+){0,3})",
        r"(SMAN\s+\d+\s*\w*)",
        r"(SMK\s+\w+(?:\s+\w+){0,3})",
        r"(MA\s+\w+(?:\s+\w+){0,3})",
        r"(Madrasah\s+Aliyah\s+\w+(?:\s+\w+){0,3})",
    ]
    for p in patterns:
        m = re.search(p, caption)
        if m:
            return m.group(1).strip()
    return None


def process_post_ner(post: dict) -> dict:
    """Jalankan NER pada satu post."""
    caption_raw = post.get("caption", "") or ""
    caption_clean = post.get("caption_clean", "") or ""

    # Gunakan caption asli untuk rule-based (huruf kapital intact)
    rule_names = extract_name_from_congratulation(caption_raw)
    heuristic_names = extract_name_heuristic(caption_raw)

    all_names, confidence = merge_names(rule_names, heuristic_names)

    # Ekstrak sekolah
    school = extract_school(caption_raw) or post.get("sekolah")

    # Prioritas nama: gunakan yang dari data.json jika tersedia
    existing_name = post.get("nama_siswa")
    if existing_name and is_valid_name(str(existing_name)):
        primary_name = existing_name
        if primary_name not in confidence:
            confidence[primary_name] = "HIGH"
        if primary_name not in all_names:
            all_names.insert(0, primary_name)
    else:
        primary_name = all_names[0] if all_names else None

    return {
        **post,
        "ner_primary_name"  : primary_name,
        "ner_all_names"     : all_names,
        "ner_confidence"    : confidence,
        "ner_school"        : school,
        "ner_name_count"    : len(all_names),
        "ner_has_name"      : bool(primary_name),
    }


def main():
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)
    print(Fore.BLUE + Style.BRIGHT + "  STEP 3: NER - EKSTRAKSI NAMA SISWA")
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("posts_relevant", data.get("posts_all", []))
    print(Fore.CYAN + f"[STEP 3] Menjalankan NER pada {len(posts):,} post...")

    processed = []
    found_name = 0
    high_conf = 0

    for i, post in enumerate(posts):
        pp = process_post_ner(post)
        processed.append(pp)

        if pp["ner_has_name"]:
            found_name += 1
        if any(v == "HIGH" for v in pp["ner_confidence"].values()):
            high_conf += 1

        if (i + 1) % 200 == 0:
            print(Fore.YELLOW + f"  → NER: {i+1:,}/{len(posts):,}")

    # Filter: hanya post dengan nama terdeteksi
    with_name = [p for p in processed if p["ner_has_name"]]

    print(Fore.GREEN + f"\n  ✔ Total diproses NER          : {len(processed):,}")
    print(Fore.GREEN + f"  ✔ Post dengan nama terdeteksi  : {found_name:,}")
    print(Fore.GREEN + f"  ✔ High confidence names         : {high_conf:,}")
    print(Fore.GREEN + f"  ✔ Post siap untuk indexing      : {len(with_name):,}")

    # Kumpulkan semua nama unik
    all_unique_names = {}
    for p in with_name:
        for name in p["ner_all_names"]:
            if name not in all_unique_names:
                all_unique_names[name] = {
                    "name"      : name,
                    "confidence": p["ner_confidence"].get(name, "LOW"),
                    "post_count": 0,
                    "school"    : p.get("ner_school") or p.get("sekolah"),
                    "posts"     : [],
                }
            all_unique_names[name]["post_count"] += 1
            all_unique_names[name]["posts"].append(p["id"])

    print(Fore.CYAN + f"\n  → Total nama unik terdeteksi: {len(all_unique_names):,}")

    output = {
        "summary"      : {**data.get("summary", {}), "names_detected": len(all_unique_names)},
        "posts"        : processed,
        "posts_with_name": with_name,
        "unique_names" : list(all_unique_names.values()),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(Fore.GREEN + f"\n  ✔ Output disimpan ke: {OUTPUT_PATH}")
    print(Fore.GREEN + "  ✔ STEP 3 SELESAI\n")
    return processed, all_unique_names


if __name__ == "__main__":
    main()
