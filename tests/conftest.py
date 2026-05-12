"""Paylaşılan pytest fixture'ları.

Her test yeni `valid_answers` kopyası alır — test izolasyonu garantili.
"""

import sys
from pathlib import Path

import pytest

# Proje kökünü sys.path'e ekle ki `import config` vs çalışsın
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import QUESTIONS  # noqa: E402


def _build_valid_answers() -> dict[str, str]:
    """73 sorunun her birine ilk geçerli seçeneği atar.

    Yaş sorusunda options=None — "20" sabitlenir (18-30 aralığında).
    """
    answers: dict[str, str] = {}
    for q in QUESTIONS:
        if q["options"]:
            answers[q["entry_id"]] = q["options"][0]
        else:
            # open_numeric (yaş)
            answers[q["entry_id"]] = "20"
    return answers


@pytest.fixture
def valid_answers() -> dict[str, str]:
    """73 entry için geçerli cevap seti. Her test yeni kopya alır."""
    return _build_valid_answers()


@pytest.fixture
def valid_answers_json(valid_answers) -> str:
    """73 entry geçerli cevapların JSON gösterimi — mock LLM yanıtları için."""
    import json
    return json.dumps(valid_answers, ensure_ascii=False)
