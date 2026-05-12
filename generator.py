"""AI ile psikolojik yaklaşıma göre form cevabı üretimi (Groq, Gemini veya Claude)."""

import json
import logging
import os
import random
import time

from config import ALL_ENTRY_IDS, DEMOGRAPHIC_SEED_POOL, MODELS, QUESTIONS
from perspectives import Perspective

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_JITTER = 0.5

_QUOTA_KEYWORDS = (
    "resource_exhausted",
    "quota",
    "rate limit",
    "rate_limit",
    "too many requests",
    " 429",
    "(429",
)


class QuotaExhaustedError(RuntimeError):
    """API kotası tükendi — retry yapmadan üst katmana sinyal verir."""


def _is_quota_error(exc: Exception) -> bool:
    """LLM SDK hatasının 429/quota-türü olup olmadığını anlar."""
    if getattr(exc, "code", None) == 429 or getattr(exc, "status_code", None) == 429:
        return True
    msg = str(exc).lower()
    return any(kw in msg for kw in _QUOTA_KEYWORDS)


def _build_user_prompt() -> str:
    """Tüm 73 soruyu tek bir prompt olarak oluşturur."""
    lines = [
        "Aşağıdaki 73 soruluk anketi doldur. KURALLAR:",
        "1. Her soru için SADECE geçerli seçeneklerden birini seç.",
        "2. Yanıtını TEK bir JSON objesi olarak ver.",
        '3. JSON formatı: {"1775105393": "Onay", "901132347": "21", ...}',
        "4. Key'ler entry_id (string), value'lar cevap (string).",
        "5. 73 sorunun TAMAMINI yanıtla, hiçbirini atlama.",
        "6. JSON dışında HİÇBİR metin yazma.",
        "",
    ]

    for q in QUESTIONS:
        if q["options"]:
            opts = " | ".join(q["options"])
            lines.append(f'{q["entry_id"]}: {q["text"]} [{opts}]')
        else:
            lines.append(f'{q["entry_id"]}: {q["text"]} [18-25 arası sayı]')

    return "\n".join(lines)


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """Groq API çağrısı (ücretsiz, hızlı). Türkçe rol-oynama için Llama 3.3 70B."""
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=MODELS["groq"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=8000,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Google Gemini API çağrısı (yeni SDK)."""
    from google import genai

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=MODELS["gemini"],
        contents=f"{system_prompt}\n\n{user_prompt}",
    )
    return response.text


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    """Anthropic Claude API çağrısı."""
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=MODELS["claude"],
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


def _detect_backend() -> str:
    """Kullanılacak AI backend'ini belirler. Öncelik: Groq > Gemini > Claude."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if groq_key and groq_key != "your-groq-api-key-here":
        return "groq"
    if gemini_key and gemini_key != "your-gemini-api-key-here":
        return "gemini"
    if anthropic_key and anthropic_key != "your-api-key-here":
        return "claude"
    raise RuntimeError(
        "API key bulunamadı! .env dosyasına GROQ_API_KEY, GEMINI_API_KEY veya "
        "ANTHROPIC_API_KEY ekleyin."
    )


def _build_seed_block(rng: random.Random) -> tuple[str, dict]:
    """Demografik seed bloğu üretir. (prompt_block, metadata) döner.

    LLM bu profili system_prompt'a eklenmiş olarak görür ve ilgili sorularda
    BU değerleri kullanır → aynı perspektifin N çağrısı N farklı profil üretir.
    """
    seed = {
        "yas": rng.choice(DEMOGRAPHIC_SEED_POOL["yas"]),
        "sinif": rng.choice(DEMOGRAPHIC_SEED_POOL["sinif"]),
        "gelir": rng.choice(DEMOGRAPHIC_SEED_POOL["gelir"]),
        "sosyal_medya_suresi": rng.choice(DEMOGRAPHIC_SEED_POOL["sosyal_medya_suresi"]),
    }
    block = (
        "DEMOGRAFİK PROFİLİN (BU YANIT İÇİN SABİT):\n"
        f"- Yaş: {seed['yas']}\n"
        f"- Sınıf: {seed['sinif']}\n"
        f"- Algılanan ekonomik düzey: {seed['gelir']}\n"
        f"- Günlük sosyal medya kullanım süresi: {seed['sosyal_medya_suresi']}\n"
        "İlgili sorularda BU değerleri kullan, diğer yanıtların bu profille tutarlı olsun."
    )
    return block, seed


def _extract_json_object(raw: str) -> dict:
    """LLM çıktısından ilk tam JSON objesini çıkarır ve parse eder.

    Markdown fence (```json ... ```), int key, fazladan whitespace tolere edilir.
    Bulunamayan/parse edilemeyen durumlarda anlamlı ValueError fırlatır.
    """
    text = raw.strip()

    if "```" in text:
        for part in text.split("```"):
            stripped = part.strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
            if stripped.startswith("{"):
                text = stripped
                break

    start = text.find("{")
    if start == -1:
        raise ValueError("LLM çıktısında JSON objesi bulunamadı")

    depth = 0
    end = -1
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        raise ValueError("Kapanmamış JSON objesi (eksik '}')")

    candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse hatası: {e.msg} (konum {e.pos})") from e


def generate_responses(
    perspective: Perspective,
    seed: int | None = None,
    sleep_fn=time.sleep,
) -> tuple[dict[str, str], dict]:
    """Bir psikolojik yaklaşıma göre 73 sorunun cevaplarını üretir.

    Args:
        perspective: Hangi yaklaşımla rol-oynanacak
        seed: Demografik seed için deterministik tohum (None → her çağrı farklı)
        sleep_fn: Test edilebilirlik için bekleme fonksiyonu (default time.sleep)

    Returns:
        (answers, metadata) — metadata içerir:
          backend, model, seed, seed_demographics, attempts
    """
    backend = _detect_backend()
    user_prompt = _build_user_prompt()

    rng = random.Random(seed)
    demo_block, demo_meta = _build_seed_block(rng)
    final_system = perspective.system_prompt + "\n\n" + demo_block

    metadata = {
        "backend": backend,
        "model": MODELS[backend],
        "seed": seed,
        "seed_demographics": demo_meta,
        "attempts": 0,
    }

    logger.info("Backend: %s, model: %s", backend, MODELS[backend])
    logger.info("Demografik seed: %s", demo_meta)

    total_attempts = MAX_RETRIES + 1
    last_error: Exception | None = None
    for attempt in range(1, total_attempts + 1):
        metadata["attempts"] = attempt
        try:
            if backend == "groq":
                raw = _call_groq(final_system, user_prompt)
            elif backend == "gemini":
                raw = _call_gemini(final_system, user_prompt)
            else:
                raw = _call_claude(final_system, user_prompt)

            raw_answers = _extract_json_object(raw)
            answers = {str(k): str(v) for k, v in raw_answers.items()}
            return _validate(answers), metadata

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            last_error = e
            if _is_quota_error(e):
                raise QuotaExhaustedError(
                    f"API kotası tükendi (backend={backend}): {e}"
                ) from e
            if attempt < total_attempts:
                wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)) + rng.uniform(0, BACKOFF_JITTER)
                logger.warning(
                    "Deneme %d/%d başarısız: %s. %.2fs bekleniyor...",
                    attempt, total_attempts, e, wait,
                )
                sleep_fn(wait)
                continue

    raise RuntimeError(
        f"{total_attempts} denemede de başarısız olundu. Son hata: {last_error}"
    )


def _normalize(text: str) -> str:
    """Noktalama ve boşluk farklarını normalize eder."""
    return text.strip().rstrip(".").rstrip(",").lower().strip()


def _fuzzy_match(answer: str, options: list[str]) -> str | None:
    """Cevabı geçerli seçeneklerle eşleştirmeye çalışır."""
    norm_answer = _normalize(answer)
    for opt in options:
        if _normalize(opt) == norm_answer:
            return opt
    for opt in options:
        if _normalize(opt).startswith(norm_answer) or norm_answer.startswith(_normalize(opt)):
            return opt
    return None


def _validate(answers: dict) -> dict[str, str]:
    """Üretilen cevapları doğrular."""
    validated = {}

    for q in QUESTIONS:
        eid = q["entry_id"]
        if eid not in answers:
            raise ValueError(f"Eksik entry_id: {eid} ({q['text'][:50]}...)")

        answer = str(answers[eid]).strip()

        if q["options"] is not None:
            if answer not in q["options"]:
                matched = _fuzzy_match(answer, q["options"])
                if matched:
                    answer = matched
                else:
                    raise ValueError(
                        f"Geçersiz cevap entry {eid}: '{answer}' "
                        f"(Geçerli: {q['options']})"
                    )
        else:
            try:
                age = int(answer)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Yaş sayısal olmalı: '{answer}'") from e
            if not (18 <= age <= 30):
                raise ValueError(f"Yaş aralık dışı: {age}")

        validated[eid] = answer

    if len(validated) != len(QUESTIONS):
        missing = set(ALL_ENTRY_IDS) - set(validated.keys())
        raise ValueError(f"Eksik entry ID'ler: {missing}")

    return validated
