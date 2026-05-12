"""submitter.submit_form HTTP integration testleri.

`responses` kütüphanesi ile fake Google Forms — gerçek network'e ÇIKMAZ.
Edge case'ler: happy path, fbzx 3 pattern, form-closed, network hatası,
ara sayfa 4xx, ara sayfa form-closed, son sayfa onay yok, GET non-200.
"""

import requests
import responses

import submitter
from submitter import submit_form

FBZX = "1234567890123456789"


# ---------------------------------------------------------------------------
# HTML üretici helper'ları
# ---------------------------------------------------------------------------

def _view_html_with_json_fbzx(fbzx: str = FBZX) -> str:
    """Pattern 1: JSON config içinde "fbzx":"..."."""
    return f'<html>var data = {{"fbzx":"{fbzx}", "other":"x"}}</html>'


def _view_html_with_hidden_input(fbzx: str = FBZX) -> str:
    """Pattern 2: gizli input."""
    return f'<html><input type="hidden" name="fbzx" value="{fbzx}"></html>'


def _view_html_with_fb_public_load_data(fbzx: str = FBZX) -> str:
    """Pattern 3: FB_PUBLIC_LOAD_DATA_ array."""
    return f'<script>FB_PUBLIC_LOAD_DATA_ = [null,null,null,"{fbzx}",null];</script>'


def _confirmation_html() -> str:
    return "<html><body>Yanıtınız kaydedildi. Teşekkürler.</body></html>"


def _intermediate_ok_html() -> str:
    """Ara sayfa POST yanıtı — onay pattern'i içermez."""
    return "<html><body>Sayfa devam ediyor</body></html>"


def _form_closed_html() -> str:
    return "<html><body>Bu form artık yanıt kabul etmiyor.</body></html>"


def _form_closed_html_english() -> str:
    return "<html><body>This form is no longer accepting responses.</body></html>"


def _add_5_page_post_chain(final_body: str) -> None:
    """5 sayfalık POST mock'u ekler — son sayfa final_body döner, gerisi ara sayfa."""
    for _ in range(4):
        responses.add(
            responses.POST, submitter.SUBMIT_URL,
            body=_intermediate_ok_html(), status=200,
        )
    responses.add(
        responses.POST, submitter.SUBMIT_URL,
        body=final_body, status=200,
    )


# ---------------------------------------------------------------------------
# Happy path — 3 fbzx pattern'i de
# ---------------------------------------------------------------------------

class TestHappyPath:
    @responses.activate
    def test_pattern1_json_fbzx(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_view_html_with_json_fbzx(), status=200,
        )
        _add_5_page_post_chain(_confirmation_html())

        result = submit_form(valid_answers)

        assert result["success"] is True
        assert result["status_code"] == 200
        assert "kaydedildi" in result["message"]
        assert len(responses.calls) == 6  # 1 GET + 5 POST

    @responses.activate
    def test_pattern2_hidden_input(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_view_html_with_hidden_input(), status=200,
        )
        _add_5_page_post_chain(_confirmation_html())

        result = submit_form(valid_answers)

        assert result["success"] is True
        assert len(responses.calls) == 6

    @responses.activate
    def test_pattern3_fb_public_load_data(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_view_html_with_fb_public_load_data(), status=200,
        )
        _add_5_page_post_chain(_confirmation_html())

        result = submit_form(valid_answers)

        assert result["success"] is True
        assert len(responses.calls) == 6

    @responses.activate
    def test_last_post_carries_fbzx_in_payload(self, valid_answers):
        """Son POST'un body'sinde fbzx ve submissionTimestamp olmalı."""
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_view_html_with_json_fbzx(), status=200,
        )
        _add_5_page_post_chain(_confirmation_html())

        submit_form(valid_answers)

        last_call = responses.calls[-1]
        body = last_call.request.body  # urlencoded string
        assert f"fbzx={FBZX}" in body
        assert "submissionTimestamp=" in body
        assert "pageHistory=0%2C1%2C2%2C3%2C4" in body


# ---------------------------------------------------------------------------
# fbzx bulunamadı
# ---------------------------------------------------------------------------

class TestFbzxMissing:
    @responses.activate
    def test_fbzx_token_yok(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body="<html>fbzx içermeyen düz HTML</html>", status=200,
        )

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert "fbzx" in result["message"].lower()
        # Hiç POST atılmamalı — sadece GET
        assert len(responses.calls) == 1


# ---------------------------------------------------------------------------
# Form kapalı (GET'te)
# ---------------------------------------------------------------------------

class TestFormClosedOnGet:
    @responses.activate
    def test_form_kapali_turkce(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_form_closed_html(), status=200,
        )

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert "kapalı" in result["message"].lower() or "kabul etmiyor" in result["message"].lower()
        assert len(responses.calls) == 1  # POST yapılmadı

    @responses.activate
    def test_form_kapali_ingilizce(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_form_closed_html_english(), status=200,
        )

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert len(responses.calls) == 1


# ---------------------------------------------------------------------------
# Network hataları
# ---------------------------------------------------------------------------

class TestNetworkErrors:
    @responses.activate
    def test_get_connection_error(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=requests.ConnectionError("DNS resolution failed"),
        )

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert result["status_code"] == 0
        assert "network" in result["message"].lower()

    @responses.activate
    def test_post_connection_error_mid_flow(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_view_html_with_json_fbzx(), status=200,
        )
        # Sayfa 0 OK, sayfa 1'de network hatası
        responses.add(
            responses.POST, submitter.SUBMIT_URL,
            body=_intermediate_ok_html(), status=200,
        )
        responses.add(
            responses.POST, submitter.SUBMIT_URL,
            body=requests.ConnectionError("connection reset"),
        )

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert "Sayfa 1" in result["message"]
        assert "network" in result["message"].lower()


# ---------------------------------------------------------------------------
# HTTP hata kodları
# ---------------------------------------------------------------------------

class TestHttpErrors:
    @responses.activate
    def test_get_returns_500(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body="<html>Internal Server Error</html>", status=500,
        )

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert result["status_code"] == 500
        assert "yüklenemedi" in result["message"]
        assert len(responses.calls) == 1

    @responses.activate
    def test_intermediate_page_4xx_fail_fast(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_view_html_with_json_fbzx(), status=200,
        )
        # Sayfa 0 OK, sayfa 1 OK, sayfa 2'de 400
        responses.add(responses.POST, submitter.SUBMIT_URL,
                      body=_intermediate_ok_html(), status=200)
        responses.add(responses.POST, submitter.SUBMIT_URL,
                      body=_intermediate_ok_html(), status=200)
        responses.add(responses.POST, submitter.SUBMIT_URL,
                      body="<html>Bad Request</html>", status=400)

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert result["status_code"] == 400
        assert "Sayfa 2" in result["message"]
        # Sayfa 3-4 POST yapılmamış olmalı
        assert len(responses.calls) == 1 + 3  # GET + 3 POST

    @responses.activate
    def test_intermediate_page_form_closed_pattern(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_view_html_with_json_fbzx(), status=200,
        )
        responses.add(responses.POST, submitter.SUBMIT_URL,
                      body=_intermediate_ok_html(), status=200)
        # Sayfa 1 yanıtı form-closed pattern içerir
        responses.add(responses.POST, submitter.SUBMIT_URL,
                      body=_form_closed_html_english(), status=200)

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert "Sayfa 1" in result["message"]
        assert "form-closed" in result["message"].lower()
        # Sayfa 2-4 POST yapılmamış olmalı
        assert len(responses.calls) == 1 + 2  # GET + 2 POST


# ---------------------------------------------------------------------------
# Son sayfa onay yok
# ---------------------------------------------------------------------------

class TestNoConfirmation:
    @responses.activate
    def test_last_page_returns_unknown_html(self, valid_answers):
        responses.add(
            responses.GET, submitter.VIEW_URL,
            body=_view_html_with_json_fbzx(), status=200,
        )
        # 5 POST'un hepsi 200 ama hiçbirinde onay pattern yok
        for _ in range(5):
            responses.add(responses.POST, submitter.SUBMIT_URL,
                          body="<html>belirsiz yanıt</html>", status=200)

        result = submit_form(valid_answers)

        assert result["success"] is False
        assert result["status_code"] == 200
        assert "başarısız" in result["message"].lower()
