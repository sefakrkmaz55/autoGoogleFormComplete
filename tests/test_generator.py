"""generator iç fonksiyon testleri.

- _extract_json_object: LLM çıktısı parse — markdown fence, fazla whitespace, nested, gevşek JSON
- _build_user_prompt: 73 sorunun tamamı + format kuralları
- _detect_backend: API key öncelik sırası (Groq > Gemini > Claude)
"""

import pytest

from generator import _build_user_prompt, _detect_backend, _extract_json_object


class TestHappyPath:
    def test_plain_json(self):
        assert _extract_json_object('{"a":1,"b":2}') == {"a": 1, "b": 2}

    def test_with_leading_whitespace(self):
        assert _extract_json_object('   \n  {"a":1}  ') == {"a": 1}

    def test_with_trailing_text_after_json(self):
        # JSON'dan sonra gelen metin ignore edilir (depth counter ilk } sonrası durur)
        assert _extract_json_object('{"a":1} ekstra metin burada') == {"a": 1}


class TestMarkdownFence:
    def test_json_in_fence_with_lang(self):
        raw = '```json\n{"k":"v"}\n```'
        assert _extract_json_object(raw) == {"k": "v"}

    def test_json_in_fence_no_lang(self):
        raw = '```\n{"k":"v"}\n```'
        assert _extract_json_object(raw) == {"k": "v"}

    def test_explanation_before_fence(self):
        raw = 'İşte cevap:\n```json\n{"a":1,"b":2}\n```\nBaşka bir not.'
        assert _extract_json_object(raw) == {"a": 1, "b": 2}


class TestNested:
    def test_nested_object(self):
        raw = '{"outer":{"inner":"v"},"sibling":1}'
        assert _extract_json_object(raw) == {"outer": {"inner": "v"}, "sibling": 1}

    def test_deeply_nested(self):
        raw = '{"a":{"b":{"c":{"d":1}}}}'
        assert _extract_json_object(raw) == {"a": {"b": {"c": {"d": 1}}}}


class TestKeyTypes:
    def test_string_keys_pass_through(self):
        # int key JSON spec'te yok ama bazı LLM'ler "123":"x" ile string verir
        assert _extract_json_object('{"123":"x"}') == {"123": "x"}

    def test_mixed_value_types(self):
        # Validator string'e cast eder, parser raw value tipini korur
        raw = '{"a":"text","b":42,"c":true,"d":null}'
        assert _extract_json_object(raw) == {"a": "text", "b": 42, "c": True, "d": None}


class TestErrors:
    def test_no_json_at_all(self):
        with pytest.raises(ValueError, match="JSON objesi bulunamadı"):
            _extract_json_object("hiç JSON yok burada")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="JSON objesi bulunamadı"):
            _extract_json_object("")

    def test_unclosed_object(self):
        with pytest.raises(ValueError, match="Kapanmamış JSON"):
            _extract_json_object('{"a":1,"b":2')

    def test_unclosed_nested_object(self):
        with pytest.raises(ValueError, match="Kapanmamış JSON"):
            _extract_json_object('{"a":{"b":1}')

    def test_malformed_json_in_braces(self):
        # Brace dengesi OK ama içerik bozuk
        with pytest.raises(ValueError, match="JSON parse hatası"):
            _extract_json_object('{"a": ,}')


class TestMultipleObjects:
    def test_first_object_extracted(self):
        # İki obje varsa depth counter ilkinde durur
        raw = '{"first":1} {"second":2}'
        assert _extract_json_object(raw) == {"first": 1}


class TestRealisticLLMOutput:
    def test_groq_style_response(self):
        # Groq genelde direkt JSON döner, bazen fence ile sarar
        raw = '```json\n{\n  "1775105393": "Onay",\n  "901132347": "21"\n}\n```'
        result = _extract_json_object(raw)
        assert result == {"1775105393": "Onay", "901132347": "21"}

    def test_gemini_style_with_preamble(self):
        # Gemini bazen kısa açıklama ile başlar
        raw = 'Here is the JSON response:\n\n```json\n{"a":1}\n```'
        assert _extract_json_object(raw) == {"a": 1}


class TestBuildUserPrompt:
    def test_contains_all_73_entry_ids(self):
        from config import QUESTIONS
        prompt = _build_user_prompt()
        for q in QUESTIONS:
            assert q["entry_id"] in prompt

    def test_contains_kurallar_header(self):
        prompt = _build_user_prompt()
        assert "KURALLAR" in prompt
        assert "JSON" in prompt
        assert "73" in prompt

    def test_options_separator_pipe(self):
        # Çok seçenekli sorular pipe ile ayrılmış olmalı
        prompt = _build_user_prompt()
        assert "Hiçbir Zaman | Nadiren | Bazen | Sıklıkla | Her Zaman" in prompt

    def test_open_numeric_question_format(self):
        # Yaş sorusu (options=None) → "[18-25 arası sayı]" işareti
        prompt = _build_user_prompt()
        assert "[18-25 arası sayı]" in prompt


class TestDetectBackend:
    def test_groq_priority(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "real-groq-key")
        monkeypatch.setenv("GEMINI_API_KEY", "real-gemini-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "real-anthropic-key")
        assert _detect_backend() == "groq"

    def test_gemini_when_no_groq(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "real-gemini-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "real-anthropic-key")
        assert _detect_backend() == "gemini"

    def test_claude_when_only_anthropic(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "real-anthropic-key")
        assert _detect_backend() == "claude"

    def test_placeholder_groq_ignored(self, monkeypatch):
        # .env.example placeholder'ları "var" sayılmaz
        monkeypatch.setenv("GROQ_API_KEY", "your-groq-api-key-here")
        monkeypatch.setenv("GEMINI_API_KEY", "real-gemini-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        assert _detect_backend() == "gemini"

    def test_placeholder_gemini_ignored(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "your-gemini-api-key-here")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "real-anthropic-key")
        assert _detect_backend() == "claude"

    def test_placeholder_anthropic_ignored(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "your-api-key-here")
        with pytest.raises(RuntimeError, match="API key bulunamadı"):
            _detect_backend()

    def test_no_keys_raises(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="API key bulunamadı"):
            _detect_backend()
