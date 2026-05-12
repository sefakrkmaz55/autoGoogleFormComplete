"""submitter._build_page_payload testleri.

Form-tipine göre payload key/value yapısı:
- checkbox: entry.SUB + entry.SUB_sentinel
- text/scale/radio: entry.SUB
- Her zaman: fvv, partialResponse, pageHistory, fbzx
- Son sayfa: + submissionTimestamp
"""

from submitter import (
    CHECKBOX_ENTRIES,
    ENTRY_TO_SUB,
    SCALE_ENTRIES,
    TEXT_ENTRIES,
    _build_page_payload,
)

FBZX = "1234567890123456789"


class TestSharedFields:
    def test_all_pages_have_fbzx_fvv_partial_history(self):
        payload = _build_page_payload(
            answers={"1775105393": "Onay"},
            page_entries=["1775105393"],
            page_history=["0"],
            fbzx=FBZX,
            is_last_page=False,
        )
        assert payload["fbzx"] == FBZX
        assert payload["fvv"] == "1"
        assert payload["partialResponse"] == f'[null,null,"{FBZX}"]'
        assert payload["pageHistory"] == "0"

    def test_page_history_is_comma_joined(self):
        payload = _build_page_payload(
            answers={"1775105393": "Onay"},
            page_entries=["1775105393"],
            page_history=["0", "1", "2"],
            fbzx=FBZX,
            is_last_page=False,
        )
        assert payload["pageHistory"] == "0,1,2"

    def test_intermediate_page_has_no_submission_timestamp(self):
        payload = _build_page_payload(
            answers={"1775105393": "Onay"},
            page_entries=["1775105393"],
            page_history=["0"],
            fbzx=FBZX,
            is_last_page=False,
        )
        assert "submissionTimestamp" not in payload

    def test_last_page_has_submission_timestamp(self):
        payload = _build_page_payload(
            answers={"168063573": "5"},  # öz-yeterlilik son entry
            page_entries=["168063573"],
            page_history=["0", "1", "2", "3", "4"],
            fbzx=FBZX,
            is_last_page=True,
        )
        assert "submissionTimestamp" in payload
        assert payload["submissionTimestamp"] == ""


class TestCheckboxEntry:
    def test_checkbox_emits_sentinel(self):
        eid = "1775105393"
        assert eid in CHECKBOX_ENTRIES
        sub = ENTRY_TO_SUB[eid]

        payload = _build_page_payload(
            answers={eid: "Onay"},
            page_entries=[eid],
            page_history=["0"],
            fbzx=FBZX,
            is_last_page=False,
        )
        assert payload[f"entry.{sub}"] == "Onay"
        assert payload[f"entry.{sub}_sentinel"] == ""


class TestTextEntry:
    def test_text_no_sentinel(self):
        eid = "901132347"  # yaş open text
        assert eid in TEXT_ENTRIES
        sub = ENTRY_TO_SUB[eid]

        payload = _build_page_payload(
            answers={eid: "21"},
            page_entries=[eid],
            page_history=["1"],
            fbzx=FBZX,
            is_last_page=False,
        )
        assert payload[f"entry.{sub}"] == "21"
        assert f"entry.{sub}_sentinel" not in payload


class TestScaleEntry:
    def test_scale_value_passes_through(self):
        # Sosyal Ağ Kullanım (1-7 ölçek)
        eid = "109920334"
        assert eid in SCALE_ENTRIES
        sub = ENTRY_TO_SUB[eid]

        payload = _build_page_payload(
            answers={eid: "5"},
            page_entries=[eid],
            page_history=["3"],
            fbzx=FBZX,
            is_last_page=False,
        )
        assert payload[f"entry.{sub}"] == "5"
        assert f"entry.{sub}_sentinel" not in payload


class TestMultipleChoiceEntry:
    def test_radio_default_branch(self):
        # Cinsiyet — checkbox/text/scale değil
        eid = "891469387"
        assert eid not in CHECKBOX_ENTRIES
        assert eid not in TEXT_ENTRIES
        assert eid not in SCALE_ENTRIES
        sub = ENTRY_TO_SUB[eid]

        payload = _build_page_payload(
            answers={eid: "Kadın"},
            page_entries=[eid],
            page_history=["1"],
            fbzx=FBZX,
            is_last_page=False,
        )
        assert payload[f"entry.{sub}"] == "Kadın"


class TestMissingAnswer:
    def test_missing_answer_emits_empty_string(self):
        # answers dict'i entry'yi içermiyorsa "" gönderilir.
        eid = "891469387"
        sub = ENTRY_TO_SUB[eid]
        payload = _build_page_payload(
            answers={},
            page_entries=[eid],
            page_history=["1"],
            fbzx=FBZX,
            is_last_page=False,
        )
        assert payload[f"entry.{sub}"] == ""


class TestFullPageStructure:
    def test_full_page_1_demographics(self, valid_answers):
        # Sayfa 1 (Kişisel Bilgi) 10 entry — hepsi payload'da olmalı
        page_1 = [
            "901132347", "891469387", "1710909935", "1976702139", "1872607800",
            "706129097", "1979041331", "780029073", "188747957", "1346132945",
        ]
        payload = _build_page_payload(
            answers=valid_answers,
            page_entries=page_1,
            page_history=["0", "1"],
            fbzx=FBZX,
            is_last_page=False,
        )
        for eid in page_1:
            sub = ENTRY_TO_SUB[eid]
            assert f"entry.{sub}" in payload
            assert payload[f"entry.{sub}"] == valid_answers[eid]
