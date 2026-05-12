# Lessons — autoGoogleFormComplete

Geçmiş hatalardan ve kullanıcı düzeltmelerinden çıkmış kalıcı kurallar. Her oturum başında okunur. Aynı hatayı iki kez yapmak için bahane yok.

---

## Kapsam & Mimari

### L1 — Form sabittir, genelleştirme yapma
- `QUESTIONS`, `ENTRY_TO_SUB`, `PAGES` Python literal olarak `config.py` içinde kalır
- Schema externalization (YAML/JSON config), "yeni form ekleme" arayüzü, generic form framework **yasak**
- Bu bir tek-form botu, kişisel sandbox — overengineering tembelliktir
- Sebep: form dead, gerçek submission beklenmiyor. Genelleştirme = harcanmış efor

### L2 — Free AI tercih sırası kesindir
- Sıra: Groq (Llama 3.3 70B Versatile) > Gemini (2.5 Flash) > Anthropic (sadece kullanıcı API key vermişse)
- Anthropic'in free tier'ı yok — varsayılan değil
- Türkçe rol-oynama kalitesi için Llama 3.3 70B, Scout 17B'den belirgin daha iyi (geçmişte test edildi)
- Gemini 2.0 deprecated, 2.5 Flash kullanılır

### L3 — Sub-agent her zaman tercih edilir
- 3+ adımlı veya keşif gerektiren işler → uygun agent çağır (`.claude/agents/` altında 6 tane var)
- Ana bağlam penceresini araştırma çıktısıyla doldurma
- Agent listesinde olmayan iş tipi (frontend, marketing) → bu projeye uygulanmaz

---

## Kod & Hata Yönetimi

### L4 — `except Exception` yutmaz, sınıflandır
- `KeyboardInterrupt` ve `SystemExit` asla yutulmaz — retry döngüsünde bile re-raise edilir
- `requests.RequestException` ayrı tutulur, network hatası generic hata değildir
- HTTP 4xx/5xx ara sayfada → fail-fast, bir sonraki sayfaya geçme
- Sessiz `continue`, sessiz `pass`, sessiz `return None` yasak

### L5 — JSON parse savunmacı yazılır
- LLM çıktısı markdown fence (```json), int key, fazladan whitespace içerebilir
- `_extract_json_object()` tek noktadan parse eder, anlamlı hata mesajı verir
- Retry mesajları stage bilgisi taşır ("generation stage 2/3 failed: ...")

### L6 — `fbzx` 3 farklı pattern'le aranır
- Hidden input, JSON config, FB_PUBLIC_LOAD_DATA — her biri fallback
- Tek pattern başarısız olunca form değişmiş demek değildir, bir sonrakini dene
- Hepsi başarısızsa açık hata mesajı: "fbzx hiçbir pattern'le bulunamadı"

### L7 — Magic number yok, sabit modül başında
- Sayfa sayısı, retry deneme sayısı, timeout süresi → modül üstünde isimli sabit
- 100 karakter satır sınırı (`ruff` config)
- Type hints public API'da zorunlu, internal'da makul

---

## Test & Doğrulama

### L8 — Çalıştığını kanıtlamadan görev kapatılmaz
- Her faz çıkışında: kanıt (smoke test çıktısı, pytest yeşili, dry-run log'u)
- "Test edilmedi ama çalışıyor olmalı" cümlesi yasak — kanıt yoksa görev açık
- Tamamlandı işaretlemeden önce: "kıdemli mühendis bunu onaylar mıydı?"

### L9 — Test izolasyonu zorunlu
- HTTP testleri `responses` library ile mock — gerçek network'e çıkan test = otomatik fail
- Fixture HTML snippet'leri `tests/fixtures/` altında dosya olarak tutulur
- Tek test < 100ms, tüm suite < 5 saniye

---

## Süreç

### L10 — Kullanıcı düzeltmesi sonrası bu dosyayı güncelle
- Kullanıcıdan herhangi bir "böyle yapma", "öyle değil", "neden X" geri bildirimi → buraya yeni satır
- Aynı kuralın tekrarını önle: ders yazılınca davranış değişir, yazmazsam ben aynı hatayı yine yaparım
- Düzeltmenin **nedeni**ni yaz (sadece kuralı değil), kenar durumda yargı yapabileyim

### L11 — Plan modu varsayılan
- 3+ adımlı veya mimari kararlı iş → plan moduna gir, kullanıcıdan onay al
- Bir şey ters giderse DUR — körü körüne devam etme, yeniden planla
- Plan sadece inşa için değil, doğrulama için de

### L12 — `except` bloğu kendi raise'lerini yutmasın
- **Why:** Faz 2 testi şu bug'ı yakaladı: `try: int(age); if not 18 <= age <= 30: raise ValueError("aralık dışı")` outer `except (ValueError, TypeError)` tarafından yakalanıyor ve "Yaş sayısal olmalı" yanıltıcı mesajıyla yeniden fırlatılıyordu. Yani 31 yaşındaki cevap "sayısal değil" diye loglanıyordu — gerçek hata kayboluyordu.
- **How to apply:** Parsing ve range check'i AYRI try bloklarında tut. `int()` parse hatası ile kendi `ValueError`'unu karıştırma. Re-raise gerekirse `raise ... from e` ile original cause koru.

### L13 — Hardcoded değerler runtime injection ile çelişir
- **Why:** `perspectives.py` `_base_prompt`'ta `"Sen 21 yaşında..."` cümlesi vardı. Faz 3'te diversity injection (runtime'da yaş 18-25 seed) eklendiğinde LLM iki bilgi alıyordu: "21 yaşındasın" + "yaş 23". Model ilk cümleye inanır, seed yok sayılır → diversity broken.
- **How to apply:** Bir veriyi runtime'da enjekte etmeyi planladığında, static prompt/config'te HARDCODED versiyonu OLMAMALI. Diversity, seed, config-driven değerler tek source'tan gelmeli.

### L14 — `logging.basicConfig` çift çağrıda no-op
- **Why:** Test'ler ardışık `main()` çağırıyordu; ikinci çağrıda log level değişmiyordu çünkü `basicConfig` root logger'da handler varsa sessizce çıkar.
- **How to apply:** Test edilebilir CLI'larda `logging.basicConfig(..., force=True)` (Python 3.8+). Üretimde de tek sefer çağrılsa bile gerekirse re-config edilebilir hale getirir.

### L15 — Agent davranışı belirsizse, küçük işi ana bağlamda yap
- **Why:** İki kez agent çağırdık (`api-tester` Faz 2 için, `devops-automator` Faz 5 için planlanan); api-tester 3.5s'de tool tamamlamadan döndü. Görev küçük + spesifikse (örn. `tests/test_submitter_integration.py` veya 3 CI dosyası) ana bağlamda yapmak agent overhead'inden daha hızlı.
- **How to apply:** Agent çağırma kararı = (görev kapsamı × bilinmezlik) > agent overhead. Standart kütüphane + net spec → direkt yaz. Büyük araştırma, paralel keşif, ana bağlamı kirletme riski → agent.

### L16 — Form schema'sı yapımcının yazımına göre, "doğru" Türkçe'ye göre değil
- **Why:** İlk gerçek submission Sayfa 1'de HTTP 400 verdi. Form'un `FB_PUBLIC_LOAD_DATA_` schema'sını dump edip karşılaştırdığımızda 1346132945 entry'sinde form yapımcısı "Kısm**et** net ancak belirsizlikler var." yazmış ("Kısmen" yerine, anlamsız typo). Biz `config.py`'da doğru Türkçe ile "Kısmen" yazdığımız için Google opsiyonu reddetti → "Lütfen yanıtınızı gözden geçirin."
- **How to apply:** Schema'yı external source'tan al, varsayma. Yeni form ekleme/güncelleme görevinde `FB_PUBLIC_LOAD_DATA_` json'ından her radio/dropdown option'unu **birebir kopyala** (whitespace + noktalama + typo dahil). Form yapımcısı sonra düzeltirse config de güncellenmeli. Validator'ün `_fuzzy_match`'i case/punctuation farkını tolere eder ama **typo'yu tolere etmez** — bu tasarım doğru, çünkü "Erkek" ve "Erkok" karıştırılmamalı.

### L17 — Gemini 2.5-flash free tier günlük limit **20 istek**, Llama 3.3 70B Versatile'ı tercih et
- **Why:** 2026-05-12 run'ında Gemini ile 13 başarılı submission'dan sonra kota doldu. 429 dönüşünde mesaj: `Quota exceeded for metric: generate_content_free_tier_requests, limit: 20, model: gemini-2.5-flash`. Bu Google'ın yakın zamanda düşürdüğü bir limit (eskiden 250 RPD idi). Ayrıca her form için ortalama ~1.5 API call gerekiyor (L16 typo bug'ı retry yaptırıyor) — yani **gerçek başarılı submission limiti gün başına ~13**. Groq Llama 3.3 70B Versatile'da pratik gün-başına submission sayısı çok daha yüksek.
- **How to apply:** Toplu submission planlandığında **Groq'u tercih et** (priority sırası zaten Groq>Gemini>Claude). Gemini'ye sadece Groq quota'sı dolduktan sonra düş. Tek bir run'da büyük `--count` planlama → Groq ile çalıştır. Eğer kullanıcı "Gemini ile çalıştır" derse açıkça hatırlat: "Gemini free-tier 20 RPD, gerçek limit ~13 submission/gün". `QuotaExhaustedError` mekanizması (generator.py) 429 yakalayıp ana döngüyü temiz kesiyor → kotalı backend'de zaman kaybı yok.

### L18 — Windows console stdout'u rich + Türkçe ile zorla utf-8'e geç
- **Why:** Background runda `> log.txt` yaparken Python sys.stdout default cp1254 (Türkçe locale) açıyor. Rich progress bar spinner Unicode (⠋ U+280B) cp1254'e encode edilemiyor → `UnicodeEncodeError` ve ana exception'ın üstüne traceback bindiriyor (gerçek hata kayboluyor). Ayrıca Türkçe karakter `İ`, `ş`, `ğ`, `ü` log dosyalarında soru işaretleriyle çıkıyordu.
- **How to apply:** Her CLI entry point'in başında `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` çağır (stderr için de). Ayrıca rich `Progress`'i `sys.stdout.isatty()` koşuluyla aktive et — file redirect senaryosunda devre dışı. Bu iki katmanlı savunma, console + log file ikisinde de temiz çıktı garantiler.
