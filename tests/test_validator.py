"""generator._validate / _fuzzy_match / _normalize testleri."""

import pytest

from generator import _fuzzy_match, _normalize, _validate


class TestNormalize:
    def test_strips_whitespace(self):
        assert _normalize("  Onay  ") == "onay"

    def test_strips_trailing_punctuation(self):
        assert _normalize("Onay.") == "onay"
        assert _normalize("Bazen,") == "bazen"

    def test_lowercases(self):
        assert _normalize("HER ZAMAN") == "her zaman"

    def test_combined(self):
        assert _normalize("  Sıklıkla.  ") == "sıklıkla"


class TestFuzzyMatch:
    def test_exact_match(self):
        opts = ["Hiçbir Zaman", "Nadiren", "Bazen"]
        assert _fuzzy_match("Bazen", opts) == "Bazen"

    def test_punctuation_tolerant(self):
        opts = ["Bazen", "Sıklıkla"]
        assert _fuzzy_match("Bazen.", opts) == "Bazen"

    def test_case_tolerant(self):
        opts = ["Kadın", "Erkek"]
        assert _fuzzy_match("kadın", opts) == "Kadın"

    def test_prefix_match(self):
        # Cevap seçeneğin prefix'i — kabul edilir
        opts = ["Hiçbir Zaman", "Nadiren"]
        assert _fuzzy_match("Hiçbir", opts) == "Hiçbir Zaman"

    def test_no_match_returns_none(self):
        opts = ["Kadın", "Erkek"]
        assert _fuzzy_match("Diğer", opts) is None


class TestValidate:
    def test_happy_path_full_dict(self, valid_answers):
        result = _validate(valid_answers)
        assert len(result) == len(valid_answers)
        # Onam checkbox
        assert result["1775105393"] == "Onay"
        # Yaş open numeric
        assert result["901132347"] == "20"

    def test_missing_entry_raises(self, valid_answers):
        del valid_answers["1775105393"]
        with pytest.raises(ValueError, match="Eksik entry_id: 1775105393"):
            _validate(valid_answers)

    def test_invalid_option_no_fuzzy_raises(self, valid_answers):
        # Cinsiyet sorusunda saçma cevap, fuzzy de kurtaramaz
        valid_answers["891469387"] = "Marsiyalı"
        with pytest.raises(ValueError, match="Geçersiz cevap entry 891469387"):
            _validate(valid_answers)

    def test_fuzzy_rescue_with_punctuation(self, valid_answers):
        # "Onay." → "Onay" fuzzy kurtarır
        valid_answers["1775105393"] = "Onay."
        result = _validate(valid_answers)
        assert result["1775105393"] == "Onay"

    def test_fuzzy_rescue_with_case(self, valid_answers):
        valid_answers["891469387"] = "kadın"
        result = _validate(valid_answers)
        assert result["891469387"] == "Kadın"

    def test_age_in_range(self, valid_answers):
        for age in ["18", "20", "25", "30"]:
            valid_answers["901132347"] = age
            result = _validate(valid_answers)
            assert result["901132347"] == age

    def test_age_below_range(self, valid_answers):
        valid_answers["901132347"] = "17"
        with pytest.raises(ValueError, match="Yaş aralık dışı"):
            _validate(valid_answers)

    def test_age_above_range(self, valid_answers):
        valid_answers["901132347"] = "31"
        with pytest.raises(ValueError, match="Yaş aralık dışı"):
            _validate(valid_answers)

    def test_age_non_numeric_raises(self, valid_answers):
        valid_answers["901132347"] = "yirmi"
        with pytest.raises(ValueError, match="Yaş sayısal olmalı"):
            _validate(valid_answers)

    def test_age_float_raises(self, valid_answers):
        # int() "20.5"'i parse edemez → ValueError
        valid_answers["901132347"] = "20.5"
        with pytest.raises(ValueError, match="Yaş sayısal olmalı"):
            _validate(valid_answers)

    def test_extra_entries_silently_ignored(self, valid_answers):
        # Spec'te olmayan entry_id'ler validator'a girdi olarak gelirse
        # zarar vermemeli — sadece QUESTIONS üzerinden iterate ediyoruz.
        valid_answers["999999999"] = "garbage"
        result = _validate(valid_answers)
        assert "999999999" not in result
        assert len(result) == len(result)  # spec uzunluğunda kalır
