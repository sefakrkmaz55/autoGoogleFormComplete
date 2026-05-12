# CLAUDE.md — Çalışma Kuralları

Bu dosya, bu proje üzerinde Claude'un (veya başka bir asistanın) nasıl çalışacağını tanımlar. Her oturum başında okunur.

---

## 1. Varsayılan Plan Modu
- Basit olmayan HER görev için plan moduna gir (3+ adım veya mimari kararlar)
- Bir şey ters giderse DUR ve yeniden planla — körü körüne devam etme
- Plan modunu sadece inşa için değil, doğrulama adımları için de kullan
- Belirsizliği azaltmak için baştan detaylı spesifikasyon yaz

## 2. Alt-Ajan Stratejisi
- Ana bağlam penceresini temiz tutmak için alt-ajanları bol bol kullan
- Araştırma, keşif ve paralel analizi alt-ajanlara yükle
- Karmaşık problemlerde alt-ajanlarla daha fazla işlem gücü harca
- Odaklı yürütme için her alt-ajana tek bir görev ver

### Bu Projedeki Alt-Ajanlar

`.claude/agents/` altında 6 odaklı agent tanımlı. Her görev başlamadan önce **doğru agent'ı seç**, yoksa ana bağlamı kirletme:

| Trigger | Agent | Dosya |
|---|---|---|
| Python refactor, modül sınır kararı, "daha zarif yol?" | **backend-architect** | `engineering/backend-architect.md` |
| LLM prompt, model upgrade, JSON parse, diversity injection | **ai-engineer** | `engineering/ai-engineer.md` |
| GitHub Actions, pyproject, pre-commit, packaging | **devops-automator** | `engineering/devops-automator.md` |
| submitter.py testleri, HTTP mock, edge case (timeout/4xx/closed form) | **api-tester** | `testing/api-tester.md` |
| Latency, throughput, retry kalibrasyonu, rate-limit ölçümü | **performance-benchmarker** | `testing/performance-benchmarker.md` |
| Model karşılaştırma (Groq vs Gemini), kalite eval, free-tier ekonomisi | **tool-evaluator** | `testing/tool-evaluator.md` |

**Kurallar:**
1. Agent seçimi belirsizse → kısa düşün, en uygun olanı seç, gerekçesini bildir
2. Bir görev birden fazla agent'a giriyorsa → sırayla çağır, her agent çıktısı bir sonrakine input
3. Yeni agent ihtiyacı doğarsa → kullanıcıya sor, `tasks/lessons.md`'ye not düş, sonra `.claude/agents/` altına yaz
4. Agent listesinde olmayan iş tipi (frontend, marketing, design...) → bu projeye uygulanmaz, direkt yap veya kullanıcıya sor

## 3. Kendini Geliştirme Döngüsü
- Kullanıcıdan HERHANGİ bir düzeltme sonrası: `tasks/lessons.md`'yi güncelle
- Aynı hatanın tekrarını önleyen kurallar yaz
- Hata oranı düşene kadar bu dersleri acımasızca geliştir
- Her oturum başında ilgili projenin derslerini gözden geçir

## 4. Tamamlanmadan Önce Doğrulama
- Çalıştığını kanıtlamadan bir görevi asla tamamlandı olarak işaretleme
- Gerektiğinde ana dal ile değişikliklerin arasındaki farkı kontrol et
- Kendine sor: **"Kıdemli bir mühendis bunu onaylar mıydı?"**
- Testleri çalıştır, logları kontrol et, doğruluğu kanıtla

## 5. Zarafet Talep Et (Dengeli)
- Basit olmayan değişikliklerde dur ve sor: "Daha zarif bir yol var mı?"
- Çözüm yamalı hissediyorsa: "Şu an bildiklerimle zarif çözümü uygula"
- Basit, bariz düzeltmelerde bunu atla — aşırı mühendislik yapma
- Sunmadan önce kendi işini sorgula

## 6. Otonom Hata Düzeltme
- Hata raporu verildiğinde: direkt düzelt. El tutulmasını bekleme
- Loglara, hatalara, başarısız testlere bak — sonra çöz
- Kullanıcıdan sıfır bağlam değişikliği gereksin
- CI testleri başarısız olunca nasıl yapılacağı söylenmeden git düzelt

---

## Görev Yönetimi

1. **Plan Önce:** `tasks/todo.md`'ye işaretlenebilir maddelerle plan yaz
2. **Planı Doğrula:** Uygulamaya başlamadan önce onayla
3. **İlerlemeyi Takip Et:** İlerledikçe maddeleri tamamlandı işaretle
4. **Değişiklikleri Açıkla:** Her adımda üst düzey özet sun
5. **Sonuçları Belgele:** `tasks/todo.md`'ye inceleme bölümü ekle
6. **Dersleri Kaydet:** Düzeltmelerden sonra `tasks/lessons.md`'yi güncelle

---

## Temel İlkeler

- **Önce Sadelik:** Her değişikliği olabildiğince basit yap. Minimal kod etkisi.
- **Tembellik Yok:** Kök nedeni bul. Geçici çözüm yok. Kıdemli standartlar.

---

## Bu Projeye Özgü Notlar

- **Form sabit, genelleştirme yok.** `QUESTIONS`, `ENTRY_TO_SUB`, `PAGES` Python literal olarak kalır. Schema externalization yapma. (Detay: `tasks/lessons.md`)
- **Free AI kullanılır.** Tercih sırası: Groq (Llama 3.3 70B) > Gemini (2.5 Flash). Anthropic free tier yok.
- Form **dead durumda**, gerçek submission'ın çalışması beklenmez — geliştirmeler hijyen, mimari, kalite odaklı.

---

## Oturum Açılış Kontrol Listesi (her seferinde)

1. `CLAUDE.md` (bu dosya) oku
2. `.claude/agents/` listele — hangi agent'lar tanımlı
3. `tasks/lessons.md` oku — geçmiş hatalar
4. `tasks/todo.md` oku — açık görevler, son inceleme notu
5. Şu anki istek hangi faza giriyor, hangi agent uygun, plan modunda mı çalışmak gerekiyor mu değerlendir
