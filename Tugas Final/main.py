"""
=============================================================
MAIN RUNNER - Full Pipeline Orchestrator
=============================================================
Menjalankan seluruh pipeline secara berurutan:
  Step 1 → Load Raw Apify JSON
  Step 2 → Preprocessing & Cleaning
  Step 3 → NER (Named Entity Recognition) Nama Siswa
  Step 4 → Indexing TF-IDF + BM25
  Step 5 → Final Scoring & Export

Usage:
  python main.py           # Jalankan semua step
  python main.py --step 3  # Jalankan hanya step tertentu
  python main.py --from 2  # Mulai dari step tertentu
=============================================================
"""

import sys
import time
import argparse
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# Tambah path pipeline ke sys.path
PIPELINE_DIR = Path(__file__).parent / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════╗
║     TUGAS FINAL - INFORMATION RETRIEVAL                      ║
║     Sistem Pencarian Siswa SMA Berprestasi                   ║
║     dari Instagram (Apify Hashtag Crawling)                  ║
║                                                              ║
║     Metode: NER + TF-IDF + BM25 + Cosine Similarity         ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(Fore.CYAN + Style.BRIGHT + banner)


def print_step_header(step: int, title: str):
    print(Fore.MAGENTA + Style.BRIGHT + f"\n{'═' * 60}")
    print(Fore.MAGENTA + Style.BRIGHT + f"  STEP {step}: {title}")
    print(Fore.MAGENTA + Style.BRIGHT + f"{'═' * 60}\n")


def run_step(step_num: int):
    """Jalankan step tertentu dari pipeline."""
    start = time.time()

    if step_num == 1:
        from step1_load_raw import main
        result = main()
    elif step_num == 2:
        from step2_preprocessing import main
        result = main()
    elif step_num == 3:
        from step3_ner_extraction import main
        result = main()
    elif step_num == 4:
        from step4_indexing_tfidf_bm25 import main
        result = main()
    elif step_num == 5:
        from step5_scoring_export import main
        result = main()
    else:
        print(Fore.RED + f"[ERROR] Step {step_num} tidak dikenal!")
        return None

    elapsed = time.time() - start
    print(Fore.GREEN + f"  ⏱  Step {step_num} selesai dalam {elapsed:.2f} detik\n")
    return result


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Information Retrieval Pipeline - Siswa Berprestasi")
    parser.add_argument("--step", type=int, help="Jalankan step tertentu (1-5)")
    parser.add_argument("--from", dest="from_step", type=int, default=1,
                        help="Mulai dari step tertentu (default: 1)")
    args = parser.parse_args()

    steps_to_run = []
    if args.step:
        steps_to_run = [args.step]
    else:
        steps_to_run = list(range(args.from_step, 6))

    step_names = {
        1: "Load Raw Apify Data",
        2: "Preprocessing & Cleaning",
        3: "NER - Ekstraksi Nama Siswa",
        4: "Indexing TF-IDF & BM25",
        5: "Scoring Akhir & Export",
    }

    print(Fore.CYAN + f"  Pipeline akan menjalankan step: {steps_to_run}")
    print(Fore.CYAN + "  " + "─" * 40)

    total_start = time.time()
    results = {}

    for step in steps_to_run:
        print_step_header(step, step_names.get(step, "Unknown"))
        try:
            result = run_step(step)
            results[step] = result
        except FileNotFoundError as e:
            print(Fore.RED + f"[ERROR] File tidak ditemukan: {e}")
            print(Fore.YELLOW + f"  → Pastikan step sebelumnya sudah dijalankan!")
            sys.exit(1)
        except ImportError as e:
            print(Fore.RED + f"[ERROR] Module tidak ditemukan: {e}")
            print(Fore.YELLOW + f"  → Jalankan: pip install -r requirements.txt")
            sys.exit(1)
        except Exception as e:
            print(Fore.RED + f"[ERROR] Step {step} gagal: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    total_elapsed = time.time() - total_start

    print(Fore.GREEN + Style.BRIGHT + "\n" + "═" * 60)
    print(Fore.GREEN + Style.BRIGHT + "  ✔ SEMUA PIPELINE BERHASIL DIJALANKAN!")
    print(Fore.GREEN + Style.BRIGHT + f"  ⏱  Total waktu: {total_elapsed:.2f} detik")
    print(Fore.GREEN + Style.BRIGHT + "═" * 60)
    print(Fore.CYAN + "\n  Output tersimpan di:")
    print(Fore.CYAN + "    data/output/hasil_siswa_berprestasi.json")
    print(Fore.CYAN + "    data/output/hasil_siswa_berprestasi.csv")
    print(Fore.CYAN + "    data/output/top100_siswa_beasiswa.csv\n")


if __name__ == "__main__":
    main()
