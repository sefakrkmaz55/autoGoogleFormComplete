"""Google Form şeması: 73 soru, entry ID'ler, seçenekler."""

import os

from dotenv import load_dotenv

load_dotenv()

FORM_ID = os.getenv("FORM_ID", "")
FORM_URL = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"

# ---------------------------------------------------------------------------
# LLM model konfigürasyonu — env değişkenleri override eder
# ---------------------------------------------------------------------------
DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "gemini": "gemini-2.5-flash",
    "claude": "claude-sonnet-4-20250514",
}

MODELS = {
    "groq": os.getenv("GROQ_MODEL") or DEFAULT_MODELS["groq"],
    "gemini": os.getenv("GEMINI_MODEL") or DEFAULT_MODELS["gemini"],
    "claude": os.getenv("ANTHROPIC_MODEL") or DEFAULT_MODELS["claude"],
}

# ---------------------------------------------------------------------------
# Ölçek tanımları
# ---------------------------------------------------------------------------
LIKERT_5_FREQUENCY = [
    "Hiçbir Zaman", "Nadiren", "Bazen", "Sıklıkla", "Her Zaman"
]

LIKERT_7_AGREEMENT = ["1", "2", "3", "4", "5", "6", "7"]

LIKERT_5_SELF = ["1", "2", "3", "4", "5"]

# ---------------------------------------------------------------------------
# 73 sorunun şeması
# ---------------------------------------------------------------------------
QUESTIONS = [
    # ── Bölüm 1: Onam ─────────────────────────────────────────────────────
    {
        "entry_id": "1775105393",
        "section": 1,
        "text": "Yukarıdaki metni okudum ve bu çalışmaya katılmayı kabul ediyorum.",
        "type": "checkbox",
        "options": ["Onay"],
    },

    # ── Bölüm 2: Kişisel Bilgi Formu ──────────────────────────────────────
    {
        "entry_id": "901132347",
        "section": 2,
        "text": "Yaşınız",
        "type": "open_numeric",
        "options": None,  # 18-30 arası sayı
    },
    {
        "entry_id": "891469387",
        "section": 2,
        "text": "Cinsiyetiniz",
        "type": "multiple_choice",
        "options": ["Kadın", "Erkek"],
    },
    {
        "entry_id": "1710909935",
        "section": 2,
        "text": "Sınıf Düzeyiniz",
        "type": "multiple_choice",
        "options": ["1.sınıf", "2.sınıf", "3.sınıf", "4.sınıf"],
    },
    {
        "entry_id": "1976702139",
        "section": 2,
        "text": "Algılanan Akademik Başarı Düzeyiniz",
        "type": "multiple_choice",
        "options": ["Düşük", "Orta", "Yüksek"],
    },
    {
        "entry_id": "1872607800",
        "section": 2,
        "text": "Ailenizin/Hanenizin Algılanan Gelir Düzeyi",
        "type": "multiple_choice",
        "options": ["Geliri giderinden az", "Geliri giderine denk", "Geliri giderinden fazla"],
    },
    {
        "entry_id": "706129097",
        "section": 2,
        "text": "Günlük Ortalama Sosyal Ağ Kullanım Süreniz",
        "type": "multiple_choice",
        "options": ["1 saatten az", "1-3 saat", "3-5 saat", "5 saatten fazla"],
    },
    {
        "entry_id": "1979041331",
        "section": 2,
        "text": "En Sık Kullandığınız Sosyal Ağ Platformu",
        "type": "multiple_choice",
        "options": ["Instagram", "LinkedIn", "Twitter/X", "TikTok"],
    },
    {
        "entry_id": "780029073",
        "section": 2,
        "text": "Sosyal Ağları Temel Kullanım Amacınız",
        "type": "multiple_choice",
        "options": [
            "Sosyal etkileşim ve arkadaşlarla iletişim",
            "Bilgi edinme ve kariyer/iş fırsatlarını takip etme",
            "Eğlence ve vakit geçirme",
            "Kendimi ifade etme ve içerik paylaşma",
        ],
    },
    {
        "entry_id": "188747957",
        "section": 2,
        "text": "Mezun olduktan sonra kendi alanınızda iş bulabileceğinize inanıyor musunuz?",
        "type": "multiple_choice",
        "options": [
            "Kesinlikle inanıyorum",
            "Kısmen inanıyorum",
            "Kararsızım",
            "İnanmıyorum",
            "Hiç inanmıyorum",
        ],
    },
    {
        "entry_id": "1346132945",
        "section": 2,
        "text": "Gelecekteki kariyer hedefleriniz netleşmiş durumda mı?",
        "type": "multiple_choice",
        "options": [
            "Evet, bir planım var.",
            "Kısmet net ancak belirsizlikler var.",  # form yapımcısının yazım hatası ("Kısmen" değil) — bilerek kopyalandı
            "Hayır, henüz ne yapacağımı bilmiyorum.",
        ],
    },

    # ── Bölüm 3: Gelecek Kaygısı Ölçeği (19 madde, 5'li Likert) ──────────
    {
        "entry_id": "1854839300",
        "section": 3,
        "text": "Yaşadığım sorunların uzun süre devam edecek olma ihtimalinden korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "1228005250",
        "section": 3,
        "text": "Gelecekte daha mutlu olacağımı düşünüyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "813113215",
        "section": 3,
        "text": "Gelecekte başarısız olmaktan korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "423301478",
        "section": 3,
        "text": "Gelecekte arzu ettiğim şeylere kavuşabileceğimi umuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "377772586",
        "section": 3,
        "text": "Hayatımda işlerin kötüye doğru gitmesinden korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "1291466084",
        "section": 3,
        "text": "Geçmiş deneyimlerim beni geleceğe iyi hazırladı",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "779246974",
        "section": 3,
        "text": "Gelecekte zorlukların üstesinden gelememekten korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "1759323562",
        "section": 3,
        "text": "Geleceğe umut ve coşku ile bakıyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "870154440",
        "section": 3,
        "text": "Her şey yolunda giderken bile, bir aksilik yaşama ihtimalinden korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "1828970229",
        "section": 3,
        "text": "Yapmayı çok istediğim şeyleri gerçekleştirmek için yeterli zamanım var",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "490739777",
        "section": 3,
        "text": "İşler iyi gittiğinde bile kötü bir şey olacak düşüncesine kapılıyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "1817013808",
        "section": 3,
        "text": "Gelecekte hedeflerimi gerçekleştirebileceğime inanıyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "86968199",
        "section": 3,
        "text": "Geleceğin ne getireceğinden korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "1858210291",
        "section": 3,
        "text": "Aileme maddi olarak iyi koşullar sunamama kaygısı yaşıyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "1146791452",
        "section": 3,
        "text": "Planlarımın yarım kalma düşüncesi beni mahvediyor",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "337033287",
        "section": 3,
        "text": "Gelecek benim için bulanık ve belirsiz görünüyor",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "1621087579",
        "section": 3,
        "text": "Ekonomik ve politik değişikliklerin geleceğimi tehdit edeceğinden korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "446700836",
        "section": 3,
        "text": "Gelecekte önemli karar alma düşüncesinden korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },
    {
        "entry_id": "7894089",
        "section": 3,
        "text": "Yakında büyük bir felaket olmasından korkuyorum",
        "type": "likert_5_frequency",
        "options": LIKERT_5_FREQUENCY,
    },

    # ── Bölüm 4: Sosyal Ağ Kullanım Amaçları Ölçeği (26 madde, 7'li) ─────
    {
        "entry_id": "109920334",
        "section": 4,
        "text": "Sosyal ağları herhangi bir sorunla ilgili çözüm yolları bulmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "197138982",
        "section": 4,
        "text": "Sosyal ağları merak ettiğim ya da ilgi duyduğum bir konu hakkında bilgi aramak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "895886629",
        "section": 4,
        "text": "Sosyal ağları görüşlerimi destekleyecek materyaller (fotoğraf, video ve yazı vb.) bulmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1171633179",
        "section": 4,
        "text": "Sosyal ağları arkadaşlarımla herhangi bir konu ya da durum hakkında işbirliği yapmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "262284396",
        "section": 4,
        "text": "Sosyal ağları ortak ilgi alanına sahip kişilerle bir araya gelmek için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1831547095",
        "section": 4,
        "text": "Sosyal ağları belli bir amaçla ilgili görev paylaşımı için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "454356370",
        "section": 4,
        "text": "Sosyal ağları sosyo-kültürel etkinlik düzenlemek için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1225003575",
        "section": 4,
        "text": "Sosyal ağları ortak bir amaç oluşturmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "492517351",
        "section": 4,
        "text": "Sosyal ağları etkinliklerden haberdar olmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1923181329",
        "section": 4,
        "text": "Sosyal ağları yeni arkadaşlıklar kurmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "775995212",
        "section": 4,
        "text": "Sosyal ağları arkadaşlarıma yüz yüze söyleyemediğim şeyleri söylemek için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "116431888",
        "section": 4,
        "text": "Sosyal ağları samimi olmadığım arkadaşlarımla iletişim kurmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "386430504",
        "section": 4,
        "text": "Sosyal ağları arkadaşlarımla sohbet etmek (anlık iletişim, sesli ve görüntülü iletişim) için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1056967668",
        "section": 4,
        "text": "Sosyal ağları arkadaşlarımla mesaj alış-verişi için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1404196491",
        "section": 4,
        "text": "Sosyal ağları iletişim bilgilerini bilmediğim arkadaşlarıma ulaşmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1878331713",
        "section": 4,
        "text": "Sosyal ağları eski arkadaşlarımı bulmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1061278347",
        "section": 4,
        "text": "Sosyal ağları arkadaşlarımla iletişimimi sürdürmek için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1827166757",
        "section": 4,
        "text": "Sosyal ağları arkadaşlarımla bağlantımı koparmamak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "2023444537",
        "section": 4,
        "text": "Sosyal ağları herhangi bir konu hakkında içerik (resim, video ve metin vb.) oluşturmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "526495543",
        "section": 4,
        "text": "Sosyal ağları görüşlerimi desteklemek için oluşturduğum görselleri (resim ve video vb.) paylaşmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1213744181",
        "section": 4,
        "text": "Sosyal ağları fotoğraf albümü oluşturmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1515366309",
        "section": 4,
        "text": "Sosyal ağları video albümü oluşturmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1426694542",
        "section": 4,
        "text": "Sosyal ağları kişisel etkinlik günlüğü oluşturmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "718591370",
        "section": 4,
        "text": "Sosyal ağları komik paylaşımlara (söz ve karikatür vb.) bakmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "1085193864",
        "section": 4,
        "text": "Sosyal ağları mutsuz olduğumda beni mutsuz eden etkenlerden uzaklaşmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },
    {
        "entry_id": "375070148",
        "section": 4,
        "text": "Sosyal ağları komik paylaşımlar (söz ve karikatür gibi) yapmak için kullanırım",
        "type": "likert_7_agreement",
        "options": LIKERT_7_AGREEMENT,
    },

    # ── Bölüm 5: Genel Öz-Yeterlilik Ölçeği (17 madde, 5'li) ────────────
    {
        "entry_id": "515826341",
        "section": 5,
        "text": "Planlar yaparken, onları hayata geçirebileceğimden eminimdir",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "1285658089",
        "section": 5,
        "text": "Sorunlarımdan biri, bir işe zamanında başlayamamamdır",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "603188905",
        "section": 5,
        "text": "Eğer bir işi ilk denemede yapamazsam, başarana kadar uğraşırım",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "262653341",
        "section": 5,
        "text": "Belirlediğim önemli hedeflere ulaşmada, pek başarılı olamam",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "1732311222",
        "section": 5,
        "text": "Her şeyi yarım bırakırım",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "2113830411",
        "section": 5,
        "text": "Zorluklarla yüz yüze gelmekten kaçınırım",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "1382893879",
        "section": 5,
        "text": "Eğer bir iş çok karmaşık görünüyorsa onu denemeye bile girişmem",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "738728442",
        "section": 5,
        "text": "Hoşuma gitmeyen bir şey yapmak zorunda kaldığımda onu bitirinceye kadar kendimi zorlarım",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "322333261",
        "section": 5,
        "text": "Bir şey yapmaya karar verdiğimde hemen işe girişirim",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "1540917059",
        "section": 5,
        "text": "Yeni bir şey denerken başlangıçta başarılı olamazsam çabucak vazgeçerim",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "60027487",
        "section": 5,
        "text": "Beklenmedik sorunlarla karşılaştığımda kolayca onların üstesinden gelemem",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "1643068819",
        "section": 5,
        "text": "Bana zor görünen yeni şeyleri öğrenmeye çalışmaktan kaçınırım",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "795389360",
        "section": 5,
        "text": "Başarısızlık benim azmimi arttırır",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "909566830",
        "section": 5,
        "text": "Yeteneklerime her zaman çok güvenmem",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "1287027500",
        "section": 5,
        "text": "Kendine güvenen biriyim",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "421187723",
        "section": 5,
        "text": "Kolayca pes ederim",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
    {
        "entry_id": "168063573",
        "section": 5,
        "text": "Hayatta karşıma çıkacak sorunların çoğuyla başedebileceğimi sanmıyorum",
        "type": "likert_5_self",
        "options": LIKERT_5_SELF,
    },
]

# entry_id → soru dict hızlı erişim
QUESTIONS_BY_ID = {q["entry_id"]: q for q in QUESTIONS}

# Tüm geçerli entry ID'leri
ALL_ENTRY_IDS = [q["entry_id"] for q in QUESTIONS]

# ---------------------------------------------------------------------------
# Diversity injection: demografik seed havuzu
# Generator runtime'da rastgele bir profil seçip system prompt'a enjekte eder
# ---------------------------------------------------------------------------
DEMOGRAPHIC_SEED_POOL = {
    "yas": list(range(18, 26)),                          # 18-25 (validator 18-30 kabul ediyor, biz 18-25 ile rol-oynama)
    "sinif": QUESTIONS_BY_ID["1710909935"]["options"],   # 1.sınıf, 2.sınıf, 3.sınıf, 4.sınıf
    "gelir": QUESTIONS_BY_ID["1872607800"]["options"],   # 3 kategori
    "sosyal_medya_suresi": QUESTIONS_BY_ID["706129097"]["options"],  # 4 kategori
}
