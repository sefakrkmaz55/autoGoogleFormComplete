"""main.py CLI testleri: argparse, --validate-only, --seed."""

import logging

import pytest

import main as main_module
from main import build_parser, main, run_single


class TestArgumentParser:
    def test_help_returns_zero(self, capsys):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0

    def test_perspective_and_all_mutually_exclusive(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--perspective", "cbt", "--all"])

    def test_perspective_or_all_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_seed_parses_to_int(self):
        parser = build_parser()
        args = parser.parse_args(["--perspective", "cbt", "--seed", "42"])
        assert args.seed == 42
        assert isinstance(args.seed, int)

    def test_default_log_level_info(self):
        parser = build_parser()
        args = parser.parse_args(["--perspective", "cbt"])
        assert args.log_level == "INFO"

    def test_validate_only_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--perspective", "cbt", "--validate-only"])
        assert args.validate_only is True


class TestValidateOnlyMode:
    def test_validate_only_no_api_call(self, monkeypatch):
        # API'yi çağırırsa testten haberdar olalım
        def boom(*a, **kw):
            raise AssertionError("API çağrısı yapılmamalıydı (validate-only)")

        monkeypatch.setattr("generator._call_groq", boom)
        monkeypatch.setattr("generator._call_gemini", boom)
        monkeypatch.setattr("generator._call_claude", boom)

        result = run_single("cbt", validate_only=True)
        assert result is True

    def test_validate_only_returns_zero_exit_code(self, monkeypatch):
        monkeypatch.setattr("generator._call_groq", lambda *a, **kw: None)
        exit_code = main(["--perspective", "cbt", "--validate-only"])
        assert exit_code == 0


class TestSeedDeterminism:
    def test_main_with_seed_returns_zero_on_success(self, monkeypatch):
        # run_single'i mock'la — gerçek API çağrısına gerek yok
        monkeypatch.setattr(main_module, "run_single", lambda *a, **kw: True)
        exit_code = main(["--perspective", "cbt", "--seed", "42", "--validate-only"])
        assert exit_code == 0

    def test_main_returns_nonzero_on_failure(self, monkeypatch):
        monkeypatch.setattr(main_module, "run_single", lambda *a, **kw: False)
        exit_code = main(["--perspective", "cbt", "--dry-run"])
        assert exit_code == 1


class TestLogLevel:
    def test_debug_level_sets_logger(self, monkeypatch):
        monkeypatch.setattr(main_module, "run_single", lambda *a, **kw: True)
        # main çağrısı logging.basicConfig'i kuracak
        main(["--perspective", "cbt", "--log-level", "DEBUG", "--validate-only"])
        assert logging.getLogger().level == logging.DEBUG

    def test_warning_level_sets_logger(self, monkeypatch):
        monkeypatch.setattr(main_module, "run_single", lambda *a, **kw: True)
        main(["--perspective", "cbt", "--log-level", "WARNING", "--validate-only"])
        assert logging.getLogger().level == logging.WARNING


class TestSaveLog:
    def test_save_log_includes_metadata(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main_module, "LOGS_DIR", str(tmp_path))
        meta = {"backend": "groq", "model": "x", "seed": 42, "attempts": 1}
        path = main_module.save_log("cbt", {"a": "1"}, {"success": True}, meta)
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["generation_metadata"] == meta
        assert data["perspective"] == "cbt"
        assert data["answers"] == {"a": "1"}

    def test_save_log_works_without_metadata(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main_module, "LOGS_DIR", str(tmp_path))
        path = main_module.save_log("cbt", {"a": "1"}, {"success": True})
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["generation_metadata"] == {}
