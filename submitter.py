"""Google Forms HTTP POST ile çok sayfalı form gönderimi."""

import re
import requests

from config import FORM_ID

BASE_URL = f"https://docs.google.com/forms/d/e/{FORM_ID}"
VIEW_URL = f"{BASE_URL}/viewform"
SUBMIT_URL = f"{BASE_URL}/formResponse"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# Form sayfalarındaki entry_id → sub_entry_id eşleşmesi
# (FB_PUBLIC_LOAD_DATA'dan çıkarıldı)
ENTRY_TO_SUB = {
    # Sayfa 0: Onam
    "1775105393": "279890521",
    # Sayfa 1: Kişisel Bilgi
    "901132347": "1640679420",
    "891469387": "1600858976",
    "1710909935": "1080961210",
    "1976702139": "385465889",
    "1872607800": "413035055",
    "706129097": "1242136520",
    "1979041331": "1973176168",
    "780029073": "536255596",
    "188747957": "374007339",
    "1346132945": "482953620",
    # Sayfa 2: Gelecek Kaygısı Ölçeği
    "1854839300": "1343906016",
    "1228005250": "2064753305",
    "813113215": "28252193",
    "423301478": "1980306334",
    "377772586": "1117064745",
    "1291466084": "1163246617",
    "779246974": "1848907781",
    "1759323562": "213106701",
    "870154440": "116980712",
    "1828970229": "2052568082",
    "490739777": "1467082884",
    "1817013808": "1961669930",
    "86968199": "1162571557",
    "1858210291": "242582678",
    "1146791452": "663068042",
    "337033287": "520254998",
    "1621087579": "1645856345",
    "446700836": "770497252",
    "7894089": "1432000502",
    # Sayfa 3: Sosyal Ağ Kullanım Amaçları
    "109920334": "916134968",
    "197138982": "622466170",
    "895886629": "2060393194",
    "1171633179": "2060756369",
    "262284396": "1730665925",
    "1831547095": "2144625438",
    "454356370": "1133408293",
    "1225003575": "1522327953",
    "492517351": "1984903319",
    "1923181329": "983741218",
    "775995212": "693106867",
    "116431888": "1735499311",
    "386430504": "1911683675",
    "1056967668": "61134857",
    "1404196491": "1715859216",
    "1878331713": "291288862",
    "1061278347": "529498867",
    "1827166757": "2081312165",
    "2023444537": "1155442355",
    "526495543": "1510819703",
    "1213744181": "282633545",
    "1515366309": "491065256",
    "1426694542": "1222986993",
    "718591370": "69881791",
    "1085193864": "1601412475",
    "375070148": "256274147",
    # Sayfa 4: Genel Öz-Yeterlilik
    "515826341": "1276467501",
    "1285658089": "1644805278",
    "603188905": "1615328772",
    "262653341": "2102646824",
    "1732311222": "1502856159",
    "2113830411": "13808435",
    "1382893879": "888581349",
    "738728442": "673956559",
    "322333261": "1435081445",
    "1540917059": "323513853",
    "60027487": "1224265003",
    "1643068819": "185538185",
    "795389360": "921677969",
    "909566830": "2020663791",
    "1287027500": "1623253135",
    "421187723": "1881521444",
    "168063573": "1006997842",
}

# Her sayfadaki entry_id'ler
PAGES = [
    # Sayfa 0: Onam
    ["1775105393"],
    # Sayfa 1: Kişisel Bilgi
    ["901132347", "891469387", "1710909935", "1976702139", "1872607800",
     "706129097", "1979041331", "780029073", "188747957", "1346132945"],
    # Sayfa 2: Gelecek Kaygısı
    ["1854839300", "1228005250", "813113215", "423301478", "377772586",
     "1291466084", "779246974", "1759323562", "870154440", "1828970229",
     "490739777", "1817013808", "86968199", "1858210291", "1146791452",
     "337033287", "1621087579", "446700836", "7894089"],
    # Sayfa 3: Sosyal Ağ Kullanım
    ["109920334", "197138982", "895886629", "1171633179", "262284396",
     "1831547095", "454356370", "1225003575", "492517351", "1923181329",
     "775995212", "116431888", "386430504", "1056967668", "1404196491",
     "1878331713", "1061278347", "1827166757", "2023444537", "526495543",
     "1213744181", "1515366309", "1426694542", "718591370", "1085193864",
     "375070148"],
    # Sayfa 4: Öz-Yeterlilik
    ["515826341", "1285658089", "603188905", "262653341", "1732311222",
     "2113830411", "1382893879", "738728442", "322333261", "1540917059",
     "60027487", "1643068819", "795389360", "909566830", "1287027500",
     "421187723", "168063573"],
]

# Checkbox olan entry'ler (type=2, tek seçenekli onay kutusu)
CHECKBOX_ENTRIES = {"1775105393"}

# Open-text (type=0) entry'ler
TEXT_ENTRIES = {"901132347"}

# Linear scale (type=5) entry'ler — Bölüm 4 ve 5
SCALE_ENTRIES = set()
for page_entries in PAGES[3:]:  # sayfa 3 ve 4
    SCALE_ENTRIES.update(page_entries)


def submit_form(answers: dict[str, str]) -> dict:
    """Cevapları Google Form'a sayfa sayfa POST eder."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # 1. İlk GET ile form token'larını al
    resp = session.get(VIEW_URL, timeout=30)
    if resp.status_code != 200:
        return {"success": False, "status_code": resp.status_code,
                "message": "Form sayfası yüklenemedi"}

    fbzx = _extract_fbzx(resp.text)
    if not fbzx:
        return {"success": False, "status_code": 0,
                "message": "fbzx token bulunamadı"}

    # 2. Her sayfa için POST gönder
    page_history = []
    for page_idx, page_entries in enumerate(PAGES):
        page_history.append(str(page_idx))
        is_last_page = (page_idx == len(PAGES) - 1)

        payload = _build_page_payload(
            answers, page_entries, page_history, fbzx, is_last_page
        )

        resp = session.post(
            SUBMIT_URL,
            data=payload,
            headers={
                "Referer": VIEW_URL,
                "Origin": "https://docs.google.com",
            },
            timeout=30,
        )

        # Son sayfa değilse devam et
        if not is_last_page:
            # Ara sayfa yanıtı — hata yoksa devam
            continue

    # 3. Son yanıtı kontrol et
    success = (
        "Yanıtınız kaydedildi" in resp.text
        or "kaydedilmiştir" in resp.text
        or "Your response has been recorded" in resp.text
        or "freebirdFormviewerViewResponseConfirmation" in resp.text
    )

    return {
        "success": success,
        "status_code": resp.status_code,
        "message": "Yanıt başarıyla kaydedildi" if success else "Gönderim başarısız olabilir",
    }


def _build_page_payload(
    answers: dict, page_entries: list, page_history: list,
    fbzx: str, is_last_page: bool
) -> dict:
    """Bir sayfa için POST payload'ı oluşturur."""
    payload = {}

    for entry_id in page_entries:
        sub_id = ENTRY_TO_SUB.get(entry_id, entry_id)
        value = answers.get(entry_id, "")

        if entry_id in CHECKBOX_ENTRIES:
            # Checkbox: entry.SUB_ID = value
            payload[f"entry.{sub_id}"] = value
            # Sentinel field
            payload[f"entry.{sub_id}_sentinel"] = ""
        elif entry_id in TEXT_ENTRIES:
            # Open text: entry.SUB_ID = value
            payload[f"entry.{sub_id}"] = value
        elif entry_id in SCALE_ENTRIES:
            # Linear scale: entry.SUB_ID = value
            payload[f"entry.{sub_id}"] = value
        else:
            # Radio button (type=2): entry.SUB_ID = value
            payload[f"entry.{sub_id}"] = value

    payload["fvv"] = "1"
    payload["partialResponse"] = f"[null,null,\"{fbzx}\"]"
    payload["pageHistory"] = ",".join(page_history)
    payload["fbzx"] = fbzx

    if is_last_page:
        payload["submissionTimestamp"] = ""

    return payload


def _extract_fbzx(html: str) -> str | None:
    """HTML'den fbzx token'ını çıkarır."""
    match = re.search(r'"fbzx"\s*:\s*"(-?\d+)"', html)
    if match:
        return match.group(1)
    match = re.search(r'name="fbzx"[^>]*value="([^"]+)"', html)
    if match:
        return match.group(1)
    return None
