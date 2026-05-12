"""CLI orchestrator: psikolojik yaklaşımlara göre Google Form doldurma botu."""

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime

from config import QUESTIONS
from generator import QuotaExhaustedError, generate_responses
from perspectives import ALL_PERSPECTIVE_NAMES, PERSPECTIVES
from submitter import submit_form

logger = logging.getLogger(__name__)

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")


def save_log(
    perspective_name: str,
    answers: dict,
    result: dict,
    metadata: dict | None = None,
) -> str:
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
        "generation_metadata": metadata or {},
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    return filepath


def run_single(
    perspective_name: str,
    *,
    dry_run: bool = False,
    validate_only: bool = False,
    seed: int | None = None,
) -> bool:
    """Tek bir yaklaşımla form doldurur ve gönderir."""
    perspective = PERSPECTIVES[perspective_name]
    logger.info("Yaklaşım: %s", perspective.turkish_name)

    if validate_only:
        # API çağrısı yok — sadece schema sağlığını test et
        from generator import _validate
        dummy_answers = {}
        for q in QUESTIONS:
            dummy_answers[q["entry_id"]] = q["options"][0] if q["options"] else "20"
        _validate(dummy_answers)
        logger.info("[VALIDATE-ONLY] Schema sağlığı OK — %d entry doğrulandı", len(dummy_answers))
        return True

    # 1. Cevap üretimi
    logger.info("AI ile cevaplar üretiliyor (seed=%s)...", seed)
    try:
        answers, gen_meta = generate_responses(perspective, seed=seed)
    except QuotaExhaustedError:
        # Kota tükendi — üst katman tüm döngüyü kessin
        raise
    except RuntimeError as e:
        logger.error("Cevap üretimi başarısız: %s", e)
        logger.error("İpucu: API key'in geçerli olduğundan emin ol (.env), kotayı kontrol et.")
        return False
    except ValueError as e:
        logger.error("Üretilen cevaplar şemaya uymuyor: %s", e)
        logger.error("İpucu: LLM model değişmiş veya prompt uzayı çok yumuşak olabilir.")
        return False

    logger.info("%d/%d soru yanıtlandı (model=%s, attempts=%d)",
                len(answers), len(QUESTIONS), gen_meta["model"], gen_meta["attempts"])

    # 2. Dry-run kontrolü
    if dry_run:
        log_path = save_log(perspective_name, answers, {"dry_run": True}, gen_meta)
        logger.info("[DRY-RUN] Cevaplar kaydedildi: %s", log_path)
        return True

    # 3. Form gönderimi
    logger.info("Form gönderiliyor...")
    result = submit_form(answers)
    log_path = save_log(perspective_name, answers, result, gen_meta)

    if result["success"]:
        logger.info("BAŞARILI — %s (HTTP %s)", result["message"], result["status_code"])
    else:
        logger.warning("BAŞARISIZ — %s (HTTP %s)", result["message"], result["status_code"])

    logger.info("Log: %s", log_path)
    return bool(result["success"])


def build_parser() -> argparse.ArgumentParser:
    """argparse parser'ı oluşturur (test edilebilirlik için ayrı fonksiyon)."""
    parser = argparse.ArgumentParser(
        description="Psikolojik yaklaşımlara göre Google Form otomatik doldurma botu",
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
        type=int, default=1,
        help="Her yaklaşım için kaç kez form doldurulacağı (varsayılan: 1)",
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Sadece cevap üret, form gönderme",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="API çağrısı yapma, sadece schema sağlığını doğrula",
    )
    parser.add_argument(
        "--seed",
        type=int, default=None,
        help="Demografik seed için tohum (deterministik tekrarlanabilirlik)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log seviyesi (varsayılan: INFO)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Windows'ta stdout/stderr default cp1254. Rich spinner (⠋ U+280B) ve Türkçe
    # log mesajları için utf-8'e zorla. errors="replace" defansif fallback.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, AttributeError):
                pass

    # Logging setup — force=True: aynı süreçte birden fazla main() çağrısında da etkili
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

    # rich varsa konsola renkli özet için kullan, yoksa standart logger yeter
    try:
        from rich.console import Console
        from rich.panel import Panel
        console: Console | None = Console()
    except ImportError:
        console = None
        Panel = None  # type: ignore[assignment]

    perspectives_to_run = ALL_PERSPECTIVE_NAMES if args.all else [args.perspective]

    if console:
        console.print(Panel.fit(
            f"[bold cyan]Yaklaşımlar:[/] {', '.join(perspectives_to_run)}\n"
            f"[bold cyan]Her biri:[/] {args.count} kez\n"
            f"[bold cyan]Mod:[/] "
            + ("validate-only" if args.validate_only else "dry-run" if args.dry_run else "live"),
            title="autoGoogleFormComplete",
        ))
    else:
        logger.info("Yaklaşımlar: %s, her biri %d kez", perspectives_to_run, args.count)

    # rich progress bar — opsiyonel, sadece interaktif TTY'de göster.
    # Background/file redirect senaryolarında spinner Unicode'u Windows cp1254
    # ile çakışıp crash'e neden olduğu için non-TTY'de devre dışı.
    if console and not args.validate_only and sys.stdout.isatty():
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TextColumn,
            TimeElapsedColumn,
        )
        progress_ctx = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        )
    else:
        progress_ctx = None

    success_count = 0
    total_count = len(perspectives_to_run) * args.count

    rng = random.Random(args.seed) if args.seed is not None else None

    def _run_iteration(p_name: str, idx: int) -> None:
        nonlocal success_count
        # Her iterasyona benzersiz ama seed-bağımlı bir tohum üret
        iter_seed = None
        if rng is not None:
            iter_seed = rng.randint(0, 2**31 - 1)
        ok = run_single(
            p_name,
            dry_run=args.dry_run,
            validate_only=args.validate_only,
            seed=iter_seed,
        )
        if ok:
            success_count += 1
        # Gönderimler arası rastgele bekleme (dry-run/validate'de bekleme yok)
        # `rng` set ise (--seed verildiyse) bekleme süresi de deterministik
        if not args.dry_run and not args.validate_only and idx < total_count - 1:
            wait = (rng or random).uniform(3, 8)
            logger.info("%.1f saniye bekleniyor...", wait)
            time.sleep(wait)

    idx = 0
    quota_hit = False
    try:
        if progress_ctx is not None:
            with progress_ctx as progress:
                for p_name in perspectives_to_run:
                    task = progress.add_task(p_name, total=args.count)
                    for _ in range(args.count):
                        _run_iteration(p_name, idx)
                        idx += 1
                        progress.update(task, advance=1)
        else:
            for p_name in perspectives_to_run:
                for _ in range(args.count):
                    _run_iteration(p_name, idx)
                    idx += 1
    except QuotaExhaustedError as e:
        quota_hit = True
        logger.warning("API kotası tükendi — döngü durduruldu: %s", e)

    if console:
        if quota_hit:
            console.print(
                f"[bold yellow]KOTA DOLDU:[/] {success_count}/{idx} başarılı, "
                f"{total_count - idx} iterasyon atlandı"
            )
        else:
            color = "green" if success_count == total_count else "yellow" if success_count else "red"
            console.print(f"[bold {color}]SONUÇ:[/] {success_count}/{total_count} başarılı")
    else:
        if quota_hit:
            logger.info(
                "KOTA DOLDU — %d/%d başarılı (toplam hedef %d, %d atlandı)",
                success_count, idx, total_count, total_count - idx,
            )
        else:
            logger.info("SONUÇ: %d/%d başarılı gönderim", success_count, total_count)

    if quota_hit:
        return 2
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
