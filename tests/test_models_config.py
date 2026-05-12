"""config.MODELS yapılandırması ve env override testleri."""

import importlib

import config


def _reload_config():
    """config modülünü reload — env değişiklikleri yeniden okunsun."""
    importlib.reload(config)
    return config


class TestDefaultModels:
    def test_defaults_present(self, monkeypatch):
        # Env var override'larını sil → DEFAULT_MODELS'a düşmeli
        monkeypatch.delenv("GROQ_MODEL", raising=False)
        monkeypatch.delenv("GEMINI_MODEL", raising=False)
        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
        cfg = _reload_config()

        assert cfg.MODELS["groq"] == cfg.DEFAULT_MODELS["groq"]
        assert cfg.MODELS["gemini"] == cfg.DEFAULT_MODELS["gemini"]
        assert cfg.MODELS["claude"] == cfg.DEFAULT_MODELS["claude"]

    def test_default_groq_is_llama_3_3(self):
        # Türkçe rol-oynama kalitesi için sabitlenmiş (L2)
        assert config.DEFAULT_MODELS["groq"] == "llama-3.3-70b-versatile"

    def test_default_gemini_is_2_5_flash(self):
        # 2.0 deprecated (L2)
        assert config.DEFAULT_MODELS["gemini"] == "gemini-2.5-flash"


class TestEnvOverride:
    def test_groq_override(self, monkeypatch):
        monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
        cfg = _reload_config()
        assert cfg.MODELS["groq"] == "llama-3.1-8b-instant"

    def test_gemini_override(self, monkeypatch):
        monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
        cfg = _reload_config()
        assert cfg.MODELS["gemini"] == "gemini-2.5-pro"

    def test_anthropic_override(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-20251010")
        cfg = _reload_config()
        assert cfg.MODELS["claude"] == "claude-opus-4-20251010"

    def test_empty_env_falls_back_to_default(self, monkeypatch):
        # Boş string default'a düşmeli (truthy değil)
        monkeypatch.setenv("GROQ_MODEL", "")
        cfg = _reload_config()
        assert cfg.MODELS["groq"] == cfg.DEFAULT_MODELS["groq"]


class TestDemographicSeedPool:
    def test_pool_has_four_dimensions(self):
        assert set(config.DEMOGRAPHIC_SEED_POOL.keys()) == {
            "yas", "sinif", "gelir", "sosyal_medya_suresi"
        }

    def test_age_range_18_to_25(self):
        ages = config.DEMOGRAPHIC_SEED_POOL["yas"]
        assert ages == list(range(18, 26))

    def test_class_options_match_question(self):
        # Pool QUESTIONS'taki gerçek options'a bağlı → tek source of truth
        sinif_pool = config.DEMOGRAPHIC_SEED_POOL["sinif"]
        sinif_q = config.QUESTIONS_BY_ID["1710909935"]
        assert sinif_pool is sinif_q["options"]

    def test_income_pool_three_categories(self):
        gelir_pool = config.DEMOGRAPHIC_SEED_POOL["gelir"]
        assert len(gelir_pool) == 3

    def test_social_media_pool_four_categories(self):
        sm_pool = config.DEMOGRAPHIC_SEED_POOL["sosyal_medya_suresi"]
        assert len(sm_pool) == 4
