# Oyun İçi Çevre Metinleri Filtreleme Planı (OCR Heuristic)

## Problem 
GTA Online menüleri açık değilken ekranın sol tarafındaki OCR okuma bölgesinde (500x800) yer alan parlak çevre yazılarının (tabelalar, oyuncu isimleri), yanlışlıkla araç isimleri gibi algılanıp OCR tarafından onaylanması nedeniyle HUD mantıksız zamanlarda ortaya çıkıyor.

## Gözlem
Oyun içerisindeki menü öğeleri, dairevi veya asimetrik çevre grafiklerinin aksine sol tarafa sıkıca hizalıdır. Ekranın sol kenarından itibaren 10-150 piksel (çözünürlüğe bağlı safezone değişebilir) arasında başlarlar.

## Çözüm Planı (Heuristik)
1. **Koordinat Filtresi:** 
   Ekranda yakalanan yazının `X` başlangıç konumu, OCR kırpım kutusu (`monitor`) içerisindeki yatay genişliğin sol %40'ından daha içerideyse (yani `x / 2 > monitor["width"] * 0.45` gibi bir şeyse) bu yazı oyundaki bir menüde olamaz, sokaktaki rastgele bir metindir diyerek reddedeceğiz.

2. **Karakter Oran ve Boyutu Filtresi:** 
   Çok büyük karakterler (örneğin kameranın tam önündeki büyük bir tabela) menü yazısı olamaz. Satır yüksekliği makul bir sınırın üzerindeyse bunu da filtreleyeceğiz.

## Değişecek Dosyalar
- `workers.py`:
  - `_run_winocr_loop()` fonksiyonunda adaylar seçilirken mevcut `c[2] >= 100` (parlaklık) kuralının yanına yatay konum (`w_first.x`) ve dikey yükseklik (`h`) kontrolleri eklenerek çevre metinleri elenecek.
  - `_run_tesseract_loop()` fonksiyonunda da benzer şekilde `x` (konum) ve genel bounding box oranlarına dair daha katı bir denetim getirilecektir.
