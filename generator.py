"""AI ile psikolojik yaklaşıma göre form cevabı üretimi (Groq, Gemini veya Claude)."""

import json
import os

from dotenv import load_dotenv

from config import QUESTIONS, ALL_ENTRY_IDS
from perspectives import Perspective

load_dotenv()

MAX_RETRIES = 2


def _build_user_prompt() -> str:
    """Tüm 73 soruyu tek bir prompt olarak oluşturur."""
    lines = [
        "Aşağıdaki 73 soruluk anketi doldur. KURALLAR:",
        "1. Her soru için SADECE geçerli seçeneklerden birini seç.",
        "2. Yanıtını TEK bir JSON objesi olarak ver.",
        "3. JSON formatı: {\"1775105393\": \"Onay\", \"901132347\": \"21\", ...}",
        "4. Key'ler entry_id (string), value'lar cevap (string).",
        "5. 73 sorunun TAMAMINI yanıtla, hiçbirini atlama.",
        "6. JSON dışında HİÇBİR metin yazma.",
        "",
    ]

    for i, q in enumerate(QUESTIONS, 1):
        if q["options"]:
            opts = " | ".join(q["options"])
            lines.append(f'{q["entry_id"]}: {q["text"]} [{opts}]')
        else:
            lines.append(f'{q["entry_id"]}: {q["text"]} [18-25 arası sayı]')

    return "\n".join(lines)


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """Groq API çağrısı (ücretsiz, hızlı)."""
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
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
        model="gemini-2.0-flash",
        contents=f"{system_prompt}\n\n{user_prompt}",
    )
    return response.text


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    """Anthropic Claude API çağrısı."""
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
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
        "API key bulunamadı! .env dosyasına GROQ_API_KEY, GEMINI_API_KEY veya ANTHROPIC_API_KEY ekleyin."
    )


def generate_responses(perspective: Perspective) -> dict[str, str]:
    """Bir psikolojik yaklaşıma göre 73 sorunun cevaplarını üretir."""
    backend = _detect_backend()
    user_prompt = _build_user_prompt()

    print(f"  Backend: {backend}")

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            if backend == "groq":
                raw = _call_groq(perspective.system_prompt, user_prompt)
            elif backend == "gemini":
                raw = _call_gemini(perspective.system_prompt, user_prompt)
            else:
                raw = _call_claude(perspective.system_prompt, user_prompt)

            raw = raw.strip()
            # JSON bloğunu çıkar
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    stripped = part.strip()
                    if stripped.startswith("json"):
                        stripped = stripped[4:].strip()
                    if stripped.startswith("{"):
                        raw = stripped
                        break

            # İlk tam JSON objesini bul
            start = raw.find("{")
            if start == -1:
                raise ValueError("JSON bulunamadı")
            depth = 0
            end = start
            for i, ch in enumerate(raw[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            raw = raw[start:end + 1]

            raw_answers = json.loads(raw)
            # Key'leri string'e çevir (model int olarak dönebilir)
            answers = {str(k): str(v) for k, v in raw_answers.items()}
            validated = _validate(answers)
            return validated

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                print(f"  [Deneme {attempt + 1} başarısız: {e}] Tekrar deneniyor...")
                continue

    raise RuntimeError(
        f"{MAX_RETRIES + 1} denemede de başarısız olundu. Son hata: {last_error}"
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
    # Kısmi eşleşme: cevap seçeneğin başlangıcıysa
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
                # Fuzzy match: noktalama/boşluk farkını tolere et
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
                if not (18 <= age <= 30):
                    raise ValueError(f"Yaş aralık dışı: {age}")
            except (ValueError, TypeError):
                raise ValueError(f"Yaş sayısal olmalı: '{answer}'")

        validated[eid] = answer

    if len(validated) != len(QUESTIONS):
        missing = set(ALL_ENTRY_IDS) - set(validated.keys())
        raise ValueError(f"Eksik entry ID'ler: {missing}")

    return validated
