"""CLI orchestrator: psikolojik yaklaşımlara göre Google Form doldurma botu."""

import argparse
import json
import os
import random
import time
from datetime import datetime

from config import QUESTIONS
from perspectives import PERSPECTIVES, ALL_PERSPECTIVE_NAMES
from generator import generate_responses
from submitter import submit_form


LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")


def save_log(perspective_name: str, answers: dict, result: dict) -> str:
    """Gönderim sonucunu JSON olarak kaydeder."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{perspective_name}_{timestamp}.json"
    filepath = os.path.join(LOGS_DIR, filename)

    log_data = {
        "perspective": perspective_name,
        "timestamp": datetime.now().isoformat(),
        "answers": answers,
        "submission_result": result,
        "question_count": len(answers),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    return filepath


def run_single(perspective_name: str, dry_run: bool = False) -> bool:
    """Tek bir yaklaşımla form doldurur ve gönderir."""
    perspective = PERSPECTIVES[perspective_name]
    print(f"\n{'='*60}")
    print(f"Yaklaşım: {perspective.turkish_name}")
    print(f"{'='*60}")

    # 1. Cevap üretimi
    print("Claude ile cevaplar üretiliyor...")
    try:
        answers = generate_responses(perspective)
    except Exception as e:
        print(f"HATA - Cevap üretimi başarısız: {e}")
        return False

    print(f"  {len(answers)}/{len(QUESTIONS)} soru yanıtlandı.")

    # 2. Dry-run kontrolü
    if dry_run:
        log_path = save_log(perspective_name, answers, {"dry_run": True})
        print(f"  [DRY-RUN] Cevaplar kaydedildi: {log_path}")
        print("  Form gönderilmedi (dry-run modu).")
        return True

    # 3. Form gönderimi
    print("Form gönderiliyor...")
    result = submit_form(answers)

    # 4. Log kayıt
    log_path = save_log(perspective_name, answers, result)

    if result["success"]:
        print(f"  BASARILI - {result['message']} (HTTP {result['status_code']})")
    else:
        print(f"  BASARISIZ - {result['message']} (HTTP {result['status_code']})")

    print(f"  Log: {log_path}")
    return result["success"]


def main():
    parser = argparse.ArgumentParser(
        description="Psikolojik yaklaşımlara göre Google Form otomatik doldurma botu"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--perspective", "-p",
        choices=ALL_PERSPECTIVE_NAMES,
        help=f"Kullanılacak psikolojik yaklaşım: {', '.join(ALL_PERSPECTIVE_NAMES)}",
    )
    group.add_argument(
        "--all", "-a",
        action="store_true",
        help="Tüm 9 yaklaşımla form doldur",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=1,
        help="Her yaklaşım için kaç kez form doldurulacağı (varsayılan: 1)",
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Sadece cevap üret, form gönderme",
    )
    args = parser.parse_args()

    perspectives_to_run = ALL_PERSPECTIVE_NAMES if args.all else [args.perspective]

    print(f"Çalıştırılacak yaklaşımlar: {perspectives_to_run}")
    print(f"Her biri {args.count} kez")
    if args.dry_run:
        print("[DRY-RUN MODU AKTIF]")
    print()

    success_count = 0
    total_count = 0

    for p_name in perspectives_to_run:
        for i in range(args.count):
            total_count += 1
            if args.count > 1:
                print(f"\n--- {p_name} #{i+1}/{args.count} ---")

            ok = run_single(p_name, dry_run=args.dry_run)
            if ok:
                success_count += 1

            # Gönderimler arası rastgele bekleme (dry-run'da bekleme yok)
            if not args.dry_run and total_count < len(perspectives_to_run) * args.count:
                wait = random.uniform(3, 8)
                print(f"  {wait:.1f} saniye bekleniyor...")
                time.sleep(wait)

    print(f"\n{'='*60}")
    print(f"SONUÇ: {success_count}/{total_count} başarılı gönderim")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
