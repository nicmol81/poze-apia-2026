# poze-apia-2026

Hartă cu poze geo-taguite, publicată pe GitHub Pages: https://nicmol81.github.io/poze-apia-2026/

## Ce e proiectul

Utilizatorul (nic.mol@gmail.com) face poze cu GPS (telefon/dispozitiv folosind un app numit "conota")
și le încarcă în Google Drive, câte un folder per zi, denumit `YYMMDD` (ex. `260902` = 2 sept 2026).
Scopul: extrage coordonatele GPS din EXIF-ul fiecărei poze și le pune ca puncte pe o hartă Leaflet,
alături de poligoanele parcelelor APIA (context: agricultură / subvenții APIA).

## Structura repo-ului

- `index.html` — pagina hărții (Leaflet). Citește `MAP_DATA` din `data.geojson.js` și parcelele din
  `parcels.geojson.js`.
- `data.geojson.js` — `const MAP_DATA = {FeatureCollection...}`. Un `Feature` per poză:
  - `geometry.coordinates` = `[lon, lat]` (rotunjit la 5 zecimale pentru intrările noi; intrările vechi
    au precizie completă float — nu contează, ambele merg)
  - `properties.name` = numele fișierului foto, fără extensie (ex. `20260902_194438`)
  - `properties.link` = link Google Drive de vizualizare: `https://drive.google.com/file/d/<FILE_ID>/view?usp=drive_link`
  - `properties.folder` = numele folderului-dată din Drive (ex. `260902`) — folosit pentru grupare/filtrare în panoul lateral
- `parcels.geojson.js` — poligoane parcele APIA (date statice, nu se ating la fluxul de poze noi)
- `scripts/gps_exif.py` — parser EXIF/GPS minimal, scris în Python pur (**fără dependențe externe**: pe
  mașina folosită inițial nu erau disponibile `exiftool`, `PIL/Pillow`, nici `pip`). Poate fi rulat
  ca CLI: `python3 scripts/gps_exif.py poza1.jpg poza2.jpg` — printează `(lat, lon)` sau `None`.

## Ultimul folder procesat

**260902** (2 sept 2026) — vezi git log pentru istoricul exact al folderelor incluse deja
(mesajele de commit sunt de forma `actualizare date: 260902` sau listează mai multe date deodată).

## Flux de lucru pentru poze noi (de urmat de orice sesiune Claude viitoare)

1. Găsește în Google Drive folderul/folderele de dată mai noi decât ultimul procesat (caută foldere
   `YYMMDD` create recent; folderul acesta era `1YWCHtMMZUMqZ4bkc7M2UP-X4BBYbbtea` pentru `260902`, dar
   ID-ul diferă la fiecare folder nou — trebuie căutat, nu presupus).
2. Descarcă fiecare `.jpg` din folder (conținutul vine ca bază64 într-un fișier JSON local când e mare;
   decodează cu `base64` în Python pentru a obține fișierul `.jpg` propriu-zis).
3. Extrage `(lat, lon)` din EXIF cu `scripts/gps_exif.py` (sau echivalent, dacă mașina curentă are
   `exiftool`/`Pillow` disponibil, poate fi mai simplu să folosești acelea).
4. Pentru fiecare poză, construiește un `Feature` GeoJSON ca mai sus (`name` = numele fișierului fără
   extensie, `link` = link Drive cu file ID-ul real, `folder` = numele folderului-dată) și adaugă-l în
   lista `features` din `data.geojson.js` (păstrează formatul JSON existent — un singur obiect
   `const MAP_DATA = {...};` pe post de fișier JS, nu JSON pur).
5. Commit + push pe `main`. GitHub Pages se rebuild-uiește automat din `main`.
6. Actualizează secțiunea "Ultimul folder procesat" din acest fișier cu noua dată, ca reper pentru
   data viitoare.

## Notă despre mediul de lucru

Nu presupune că `exiftool`, `Pillow`/`PIL` sau `pip` sunt instalate pe mașina curentă — pe mașina
originală (Linux, fără acces la instalare pachete) niciunul nu era disponibil, de-asta există
`scripts/gps_exif.py` ca fallback fără dependențe. Verifică întâi dacă uneltele native sunt disponibile
(mai rapide/mai robuste), și folosește scriptul din repo doar dacă nu sunt.
