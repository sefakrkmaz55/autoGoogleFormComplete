"""generator._build_seed_block diversity injection + retry backoff testleri."""

import random

import pytest

import generator
from generator import _build_seed_block, generate_responses
from perspectives import PERSPECTIVES


class TestSeedBlockOutput:
    def test_returns_block_and_meta_tuple(self):
        rng = random.Random(42)
        block, meta = _build_seed_block(rng)
        assert isinstance(block, str)
        assert isinstance(meta, dict)

    def test_meta_has_four_keys(self):
        rng = random.Random(42)
        _, meta = _build_seed_block(rng)
        assert set(meta.keys()) == {"yas", "sinif", "gelir", "sosyal_medya_suresi"}

    def test_block_contains_demographic_values(self):
        rng = random.Random(123)
        block, meta = _build_seed_block(rng)
        # Her seçilen değer prompt bloğunda görünmeli
        assert str(meta["yas"]) in block
        assert meta["sinif"] in block
        assert meta["gelir"] in block
        assert meta["sosyal_medya_suresi"] in block

    def test_block_has_instruction_header(self):
        rng = random.Random(0)
        block, _ = _build_seed_block(rng)
        assert "DEMOGRAFİK PROFİLİN" in block
        assert "tutarlı" in block.lower()


class TestDeterminism:
    def test_same_seed_same_output(self):
        # Aynı seed → aynı demografik profil (test izolasyonu için kritik)
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        _, meta1 = _build_seed_block(rng1)
        _, meta2 = _build_seed_block(rng2)
        assert meta1 == meta2

    def test_different_seeds_likely_different(self):
        # 100 farklı seed'de en az 5 farklı meta beklenir (4-boyutlu uzay)
        seen = set()
        for s in range(100):
            _, meta = _build_seed_block(random.Random(s))
            seen.add(tuple(sorted(meta.items())))
        assert len(seen) >= 5


class TestPoolBounds:
    def test_age_within_pool(self):
        from config import DEMOGRAPHIC_SEED_POOL
        rng = random.Random(7)
        _, meta = _build_seed_block(rng)
        assert meta["yas"] in DEMOGRAPHIC_SEED_POOL["yas"]

    def test_class_within_pool(self):
        from config import DEMOGRAPHIC_SEED_POOL
        rng = random.Random(7)
        _, meta = _build_seed_block(rng)
        assert meta["sinif"] in DEMOGRAPHIC_SEED_POOL["sinif"]

    def test_income_within_pool(self):
        from config import DEMOGRAPHIC_SEED_POOL
        rng = random.Random(7)
        _, meta = _build_seed_block(rng)
        assert meta["gelir"] in DEMOGRAPHIC_SEED_POOL["gelir"]

    def test_social_media_within_pool(self):
        from config import DEMOGRAPHIC_SEED_POOL
        rng = random.Random(7)
        _, meta = _build_seed_block(rng)
        assert meta["sosyal_medya_suresi"] in DEMOGRAPHIC_SEED_POOL["sosyal_medya_suresi"]


class TestRetryBackoff:
    """generate_responses retry path — sleep_fn ve _call_* mock'larıyla."""

    def test_succeeds_on_first_try_no_sleep(self, monkeypatch, valid_answers_json):
        monkeypatch.setenv("GROQ_API_KEY", "real-key")
        monkeypatch.setattr(generator, "_call_groq", lambda sp, up: valid_answers_json)

        sleeps = []
        answers, meta = generate_responses(
            PERSPECTIVES["cbt"], seed=42, sleep_fn=sleeps.append,
        )
        assert len(answers) == 73
        assert meta["attempts"] == 1
        assert meta["backend"] == "groq"
        assert sleeps == []  # ilk denemede başarılı → uyku yok

    def test_retries_then_succeeds(self, monkeypatch, valid_answers_json):
        monkeypatch.setenv("GROQ_API_KEY", "real-key")

        call_count = {"n": 0}

        def flaky(sp, up):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise RuntimeError("Geçici LLM hatası")
            return valid_answers_json

        monkeypatch.setattr(generator, "_call_groq", flaky)

        sleeps = []
        answers, meta = generate_responses(
            PERSPECTIVES["cbt"], seed=42, sleep_fn=sleeps.append,
        )
        assert len(answers) == 73
        assert meta["attempts"] == 3
        # 2 başarısız deneme → 2 uyku çağrısı
        assert len(sleeps) == 2
        # Exponential backoff: 1s civarı, 2s civarı (+ jitter < 0.5)
        assert 1.0 <= sleeps[0] < 1.5
        assert 2.0 <= sleeps[1] < 2.5

    def test_all_retries_fail_raises_runtime(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "real-key")
        monkeypatch.setattr(generator, "_call_groq",
                            lambda sp, up: (_ for _ in ()).throw(RuntimeError("Hep fail")))

        sleeps = []
        with pytest.raises(RuntimeError, match="denemede de başarısız"):
            generate_responses(PERSPECTIVES["cbt"], seed=42, sleep_fn=sleeps.append)
        # 3 deneme = MAX_RETRIES(2) + 1; aralarda 2 uyku
        assert len(sleeps) == 2

    def test_keyboard_interrupt_propagates(self, monkeypatch):
        """L4: KeyboardInterrupt retry'de yutulmaz."""
        monkeypatch.setenv("GROQ_API_KEY", "real-key")

        def interrupted(sp, up):
            raise KeyboardInterrupt()

        monkeypatch.setattr(generator, "_call_groq", interrupted)

        with pytest.raises(KeyboardInterrupt):
            generate_responses(PERSPECTIVES["cbt"], seed=42, sleep_fn=lambda s: None)

    def test_seed_metadata_in_return(self, monkeypatch, valid_answers_json):
        monkeypatch.setenv("GROQ_API_KEY", "real-key")
        monkeypatch.setattr(generator, "_call_groq", lambda sp, up: valid_answers_json)

        _, meta = generate_responses(
            PERSPECTIVES["cbt"], seed=12345, sleep_fn=lambda s: None,
        )
        assert meta["seed"] == 12345
        assert "seed_demographics" in meta
        assert set(meta["seed_demographics"].keys()) == {
            "yas", "sinif", "gelir", "sosyal_medya_suresi"
        }
