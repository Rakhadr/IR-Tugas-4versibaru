"""
=============================================================
TUGAS JURNAL - GROUND TRUTH GENERATOR
=============================================================
Membuat ground truth data untuk evaluasi Information Retrieval.
Setiap siswa dalam dataset diklasifikasikan secara semi-otomatis
berdasarkan validitas nama (menghilangkan false positive NER) dan
kesesuaian kriteria (siswa SMA dan memiliki prestasi nyata).

Kriteria Kelayakan (Relevansi = 1):
  - Nama valid (bukan kata sandang, kata hubung, atau frasa umum)
  - Jenjang sekolah adalah SMA/SMK/MA/SMAN/SMKN/MAN (bukan SD/SMP/Universitas)
  - Memiliki prestasi nyata yang tertulis di caption/juara (bukan sekadar peserta simulasi)
=============================================================
"""

import json
import re
import pandas as pd
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# Path definition
BASE_DIR        = Path(__file__).resolve().parent
PATH_BASELINE   = BASE_DIR.parent / "Tugas Final" / "data" / "output" / "hasil_siswa_berprestasi.json"
OUTPUT_GT_CSV   = BASE_DIR / "data" / "ground_truth.csv"

# Daftar stopwords untuk nama (false positive NER)
INVALID_NAME_KEYWORDS = [
    "dalam", "menimba", "ilmu", "menerima", "apresiasi", "sobat", "smansaku", 
    "yang", "sebagai", "bentuk", "siswi", "hebat", "ananda", "siswa", "peserta",
    "pemenang", "official", "panitia", "tim", "kontingen", "guru", "kepala", 
    "sekolah", "keluarga", "besar", "alumni", "panitia", "pembina", "pendamping",
    "apresiasi langsung", "uji coba", "simulasi", "try out", "telah berhasil",
    "selamat kepada", "selamat", "sukses", "untuk", "ananda", "dan", "atau",
    "kembali", "kembali terukir", "prestasi", "juara"
]

# Daftar keywords tingkat sekolah menengah (SMA/SMK/MA)
HIGH_SCHOOL_KEYWORDS = ["sma", "smk", "ma ", "man ", "sman", "smkn", "aliyah", "kejuruan", "slta"]
JUNIOR_SCHOOL_KEYWORDS = ["smp", "sd ", "sdn", "smpn", "mts", "tsanawiyah", "dasar", "kanak"]

def is_valid_name(name: str) -> bool:
    """Memeriksa apakah nama terdeteksi valid atau false positive NER."""
    if not name or len(name) < 3:
        return False
    
    name_lower = name.lower().strip()
    
    # 1. Cek keyword blacklist
    for kw in INVALID_NAME_KEYWORDS:
        if kw == name_lower or name_lower.startswith(kw + " ") or name_lower.endswith(" " + kw):
            return False
            
    # 2. Cek pola umum false positive NER (panjang berlebihan atau kata tunggal yang umum)
    if len(name.split()) > 5: # Nama orang jarang lebih dari 5 kata
        return False
        
    return True

def is_high_school_student(school: str, caption: str) -> bool:
    """Memeriksa apakah sekolah adalah tingkat SMA dan bukan SMP/SD/Univ."""
    school_lower = str(school).lower() if school else ""
    caption_lower = str(caption).lower() if caption else ""
    
    # Cek jika ada indikasi SMP/SD di nama sekolah
    for kw in JUNIOR_SCHOOL_KEYWORDS:
        if kw in school_lower:
            return False
            
    # Cek jika ada indikasi SMA di nama sekolah
    for kw in HIGH_SCHOOL_KEYWORDS:
        if kw in school_lower or kw in caption_lower:
            return True
            
    # Default jika tidak ada informasi sekolah, anggap relevan jika tidak ada kata kunci SMP/SD
    if not school_lower:
        # Cek apakah ada kata kunci SMP/SD di caption
        for kw in JUNIOR_SCHOOL_KEYWORDS:
            if kw in caption_lower:
                return False
        return True # Default assume SMA/relevance unless proven otherwise
        
    return False

def has_real_achievement(prestasi: str, caption: str) -> bool:
    """Memeriksa apakah siswa memiliki prestasi nyata, bukan hanya peserta simulasi/uji coba."""
    prestasi_lower = str(prestasi).lower() if prestasi else ""
    caption_lower = str(caption).lower() if caption else ""
    
    # Kata kunci uji coba/simulasi tanpa prestasi nyata
    if "simulasi" in caption_lower or "uji coba" in caption_lower or "gladi" in caption_lower or "try out" in caption_lower or "tryout" in caption_lower:
        # Kecuali jika dia benar-benar memenangkan/meraih juara
        if not ("juara" in prestasi_lower or "medali" in prestasi_lower or "peraih" in prestasi_lower or "pemenang" in prestasi_lower):
            return False
            
    # Cek kata kunci prestasi nyata
    achievement_keywords = ["juara", "medali", "perunggu", "perak", "emas", "podium", "peringkat", "pemenang", "lulus", "lolos", "award", "terbaik"]
    for kw in achievement_keywords:
        if kw in prestasi_lower or kw in caption_lower:
            return True
            
    return False

def main():
    print(Fore.BLUE + Style.BRIGHT + "=== TUGAS JURNAL: GENERATE GROUND TRUTH ===")
    
    if not PATH_BASELINE.exists():
        print(Fore.RED + f"[ERROR] File baseline tidak ditemukan di: {PATH_BASELINE}")
        print(Fore.RED + "Jalankan pipeline Tugas Final terlebih dahulu!")
        return

    with open(PATH_BASELINE, "r", encoding="utf-8") as f:
        data = json.load(f)

    students = data.get("students", [])
    print(Fore.CYAN + f"  Memproses {len(students)} data siswa untuk pelabelan ground truth...")

    gt_records = []
    
    for s in students:
        name = s["nama_siswa"]
        school = s.get("sekolah", "")
        prestasi = s.get("prestasi", "")
        caption = s.get("best_post_snippet", "")
        
        # Evaluasi kriteria relevansi
        valid_name = is_valid_name(name)
        high_school = is_high_school_student(school, caption)
        achievement = has_real_achievement(prestasi, caption)
        
        # Ground Truth Label
        relevance = 1 if (valid_name and high_school and achievement) else 0
        
        # Alasan pelabelan untuk auditability
        reasons = []
        if not valid_name: reasons.append("False positive NER / invalid name pattern")
        if not high_school: reasons.append("Bukan jenjang SMA (SD/SMP/Univ/Tidak terdeteksi)")
        if not achievement: reasons.append("Tidak ada bukti prestasi nyata (mis. hanya peserta uji coba)")
        
        reason_str = "RELEVAN" if relevance == 1 else "TIDAK RELEVAN: " + ", ".join(reasons)

        gt_records.append({
            "nama_siswa": name,
            "sekolah": school or "-",
            "prestasi": prestasi or "-",
            "relevance_ground_truth": relevance,
            "status_label": reason_str,
            "snippet": caption[:100]
        })

    # Save to CSV
    df_gt = pd.DataFrame(gt_records)
    OUTPUT_GT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_gt.to_csv(OUTPUT_GT_CSV, index=False, encoding="utf-8-sig")
    
    # Print stats
    total = len(df_gt)
    relevan_count = len(df_gt[df_gt["relevance_ground_truth"] == 1])
    irelevan_count = total - relevan_count
    
    print(Fore.GREEN + f"\n  ✔ Ground Truth berhasil dibuat di: {OUTPUT_GT_CSV}")
    print(Fore.GREEN + f"  ✔ Total siswa berlabel: {total}")
    print(Fore.GREEN + f"  ✔ Relevan (Siswa SMA Berprestasi): {relevan_count} ({relevan_count/total*100:.1f}%)")
    print(Fore.GREEN + f"  ✔ Tidak Relevan (False Positive/Non-SMA): {irelevan_count} ({irelevan_count/total*100:.1f}%)")
    
    # Show top relevan and top non-relevan samples
    print(Fore.BLUE + Style.BRIGHT + "\n--- CONTOH SISWA RELEVAN (Label 1) ---")
    for idx, row in df_gt[df_gt["relevance_ground_truth"] == 1].head(5).iterrows():
        print(f"  - {row['nama_siswa']} | Sekolah: {row['sekolah']} | Prestasi: {row['prestasi']}")
        
    print(Fore.RED + Style.BRIGHT + "\n--- CONTOH SISWA TIDAK RELEVAN (Label 0) ---")
    for idx, row in df_gt[df_gt["relevance_ground_truth"] == 0].head(5).iterrows():
        print(f"  - {row['nama_siswa']} | Alasan: {row['status_label']}")

if __name__ == "__main__":
    main()
