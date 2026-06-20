"""
=============================================================
STEP 1 - LOAD & VALIDASI DATA MENTAH APIFY
=============================================================
Referensi:
  - Apify Instagram Hashtag Scraper API
  - Zarrella, D. (2010). The Social Media Marketing Book. O'Reilly.
  - Kausar, A. et al. (2019). Web Scraping using Python. IJCA.
=============================================================
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "data" / "raw" / "raw_posts_apify.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "step1_loaded.json"


def load_raw_apify(path: Path) -> list:
    """
    Memuat data mentah hasil scraping Apify Instagram Hashtag Crawler.
    Format: JSON array dengan field Instagram post.
    """
    print(Fore.CYAN + f"[STEP 1] Memuat data mentah dari: {path}")
    if not path.exists():
        print(Fore.RED + f"[ERROR] File tidak ditemukan: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(Fore.GREEN + f"  ✔ Total post dimuat: {len(data):,}")
    return data


def validate_schema(posts: list) -> list:
    """
    Validasi dan standarisasi skema field JSON dari Apify output.
    Field wajib: id, caption, ownerFullName, ownerUsername, hashtags, timestamp
    """
    required_fields = ["id", "caption", "ownerFullName", "ownerUsername",
                       "hashtags", "timestamp", "_scraped_hashtag"]
    valid = []
    skipped = 0

    for post in posts:
        # Isi default jika field kosong
        for field in required_fields:
            if field not in post:
                post[field] = None

        # Skip post tanpa caption (tidak bisa di-analisis)
        if not post.get("caption"):
            skipped += 1
            continue

        # Normalisasi field
        post["caption"] = post["caption"].strip()
        post["ownerFullName"] = post.get("ownerFullName") or ""
        post["ownerUsername"] = post.get("ownerUsername") or ""
        post["likesCount"] = post.get("likesCount", 0) or 0
        post["commentsCount"] = post.get("commentsCount", 0) or 0
        post["hashtags"] = post.get("hashtags") or []
        post["_scraped_hashtag"] = post.get("_scraped_hashtag") or ""

        valid.append(post)

    print(Fore.YELLOW + f"  → Post dengan caption valid  : {len(valid):,}")
    print(Fore.YELLOW + f"  → Post dilewati (tanpa caption): {skipped:,}")
    return valid


def extract_summary(posts: list) -> dict:
    """Statistik ringkasan data mentah."""
    hashtags_set = set()
    for p in posts:
        for ht in (p.get("hashtags") or []):
            hashtags_set.add(ht.lower())

    return {
        "total_posts"      : len(posts),
        "unique_hashtags"  : len(hashtags_set),
        "scraped_hashtags" : list(set(p["_scraped_hashtag"] for p in posts if p["_scraped_hashtag"])),
        "date_range"       : {
            "earliest": min((p["timestamp"] for p in posts if p.get("timestamp")), default="-"),
            "latest"  : max((p["timestamp"] for p in posts if p.get("timestamp")), default="-"),
        },
        "processed_at": datetime.now().isoformat(),
    }


def main():
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)
    print(Fore.BLUE + Style.BRIGHT + "  STEP 1: LOAD & VALIDASI DATA MENTAH APIFY")
    print(Fore.BLUE + Style.BRIGHT + "=" * 60)

    # 1. Load
    raw_posts = load_raw_apify(RAW_PATH)

    # 2. Validasi
    valid_posts = validate_schema(raw_posts)

    # 3. Ringkasan
    summary = extract_summary(valid_posts)
    print(Fore.CYAN + "\n[RINGKASAN DATA]")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # 4. Simpan
    output = {"summary": summary, "posts": valid_posts}
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(Fore.GREEN + f"\n  ✔ Output disimpan ke: {OUTPUT_PATH}")
    print(Fore.GREEN + "  ✔ STEP 1 SELESAI\n")
    return valid_posts


if __name__ == "__main__":
    main()
