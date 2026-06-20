"""
=============================================================
MASTER RUNNER - RUN ALL EXPERIMENTS
=============================================================
Menjalankan seluruh alur eksperimen perbandingan secara urut:
  1. Jalankan LLM Pretrained Pipeline
  2. Jalankan Analisis Korelasi & Perbandingan Peringkat
  3. Jalankan Generator Ground Truth
  4. Jalankan Evaluasi Metrik Kinerja Temu Kembali (IR)
=============================================================
"""

import subprocess
import sys
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

BASE_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = BASE_DIR / "Tugas Final" / "venv" / "bin" / "python"

if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable) # fallback ke python saat ini jika venv tidak ada

def run_script(script_path: Path):
    print(Fore.YELLOW + f"\n[RUNNING] {script_path.name}...")
    result = subprocess.run([str(VENV_PYTHON), str(script_path)], capture_output=False, text=True)
    if result.returncode == 0:
        print(Fore.GREEN + f"[SUCCESS] {script_path.name} selesai.\n")
    else:
        print(Fore.RED + f"[FAILED] {script_path.name} gagal dengan exit code {result.returncode}.\n")
        sys.exit(result.returncode)

def main():
    print(Fore.BLUE + Style.BRIGHT + """
╔═══════════════════════════════════════════════════════════╗
║   MASTER RUNNER — EKSPERIMEN PERBANDINGAN IR              ║
║   Baseline vs LLM Pretrained Embeddings                   ║
╚═══════════════════════════════════════════════════════════╝
""")

    # 1. LLM Pipeline
    llm_script = BASE_DIR / "Tugas Pembanding" / "llm_pipeline.py"
    run_script(llm_script)

    # 2. Comparison
    comp_script = BASE_DIR / "Tugas Pembanding" / "comparison.py"
    run_script(comp_script)

    # 3. Ground Truth Generator
    gt_script = BASE_DIR / "Tugas Jurnal" / "generate_ground_truth.py"
    run_script(gt_script)

    # 4. Evaluation Metrics
    eval_script = BASE_DIR / "Tugas Jurnal" / "evaluation.py"
    run_script(eval_script)

    print(Fore.GREEN + Style.BRIGHT + """
🎉 SELURUH ALUR EKSPERIMEN BERHASIL DIJALANKAN!
   - Hasil LLM disimpan di: Tugas Pembanding/data/output/
   - Analisis korelasi di: Tugas Pembanding/data/output/
   - Ground Truth & Metrik IR di: Tugas Jurnal/data/
   - Grafik Metrik IR di: Tugas Jurnal/plots/
   - Draf Jurnal Scopus di: Tugas Jurnal/paper/jurnal_siswa_berprestasi.md
""")

if __name__ == "__main__":
    main()
