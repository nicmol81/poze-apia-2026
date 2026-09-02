# poze-apia-2026

Hartă cu poze geo-taguite, publicată pe GitHub Pages: https://nicmol81.github.io/poze-apia-2026/

## Ce e proiectul

Utilizatorul (nic.mol@gmail.com) face poze cu GPS (telefon/dispozitiv folosind un app numit "conota")
și le încarcă în Google Drive, câte un folder per zi, denumit `YYMMDD` (ex. `260902` = 2 sept 2026).
Scopul: extrage coordonatele GPS din EXIF-ul fiecărei poze și le pune ca puncte pe o hartă Leaflet,
alături de poligoanele parcelelor APIA (context: agricultură / subvenții APIA).

**Folderul-părinte din Drive** care conține toate folderele zilnice de poze:
`1oRkDH1j18KX5K9DZZdcGhJH9kWyYXRNK` ("poze APIA 2026", owner `pozeapia2026@gmail.com`, partajat cu
`nic.mol@gmail.com`). Caută foldere noi `YYMMDD` direct ca fii ai acestui folder (`parentId = '...'`),
nu e nevoie de o căutare mai largă în tot Drive-ul.

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
  Funcționează pe orice fișier `.jpg` local, indiferent cum a ajuns acolo (fișier întreg sau doar
  un prefix — vezi mai jos).
- `scripts/fetch_gps_fast.py` — **metoda RECOMANDATĂ, de folosit implicit** pentru poze noi din Drive.
  Vezi secțiunea „Metoda rapidă" mai jos pentru de ce există și cum funcționează.

## Ultimul folder procesat

**260902** (2 sept 2026) — complet procesat, toate cele 47 de poze din folder sunt pe hartă. Vezi git
log pentru istoricul exact al folderelor incluse deja (mesajele de commit sunt de forma
`actualizare date: 260902` sau listează mai multe date deodată).

## Flux de lucru pentru poze noi (de urmat de orice sesiune Claude viitoare)

1. Găsește în Google Drive folderul/folderele de dată mai noi decât ultimul procesat: listează fiii
   folderului-părinte `1oRkDH1j18KX5K9DZZdcGhJH9kWyYXRNK` (vezi mai sus) și alege cele cu nume `YYMMDD`
   mai mari decât ultimul procesat. ID-ul folderului zilnic diferă de fiecare dată — nu-l presupune.
2. Pentru fiecare poză, extrage `(lat, lon)` cu **`scripts/fetch_gps_fast.py`** (vezi secțiunea „Metoda
   rapidă" mai jos) — NU folosi tool-ul MCP `download_file_content` pentru asta, e mult mai lent și
   consumă mult mai mulți tokeni pentru același rezultat (vezi de ce, mai jos). Foloseste tool-ul MCP
   doar ca fallback, dacă `fetch_gps_fast.py` eșuează pentru o poză anume (ex. fișierul nu mai e
   partajat public) — în acel caz descarcă fișierul întreg prin MCP și decodează base64 din JSON-ul
   salvat local, apoi rulează `scripts/gps_exif.py` pe el.
3. (inclus în pasul 2 dacă folosești `fetch_gps_fast.py`)
4. Pentru fiecare poză, construiește un `Feature` GeoJSON ca mai sus (`name` = numele fișierului fără
   extensie, `link` = link Drive cu file ID-ul real, `folder` = numele folderului-dată) și adaugă-l în
   lista `features` din `data.geojson.js` (păstrează formatul JSON existent — un singur obiect
   `const MAP_DATA = {...};` pe post de fișier JS, nu JSON pur).
5. Commit + push pe `main`. GitHub Pages se rebuild-uiește automat din `main`.
6. Actualizează secțiunea "Ultimul folder procesat" din acest fișier cu noua dată, ca reper pentru
   data viitoare.

## Metoda rapidă de extragere GPS (folosește-o implicit, nu tool-ul MCP Drive)

**Problemă descoperită pe 2 sept 2026, la procesarea a 43 de poze deodată:** tool-ul MCP
`download_file_content` (Google Drive) descarcă fișierul JPEG *întreg* (6-8 MB per poză la telefoanele
folosite aici) și-l codează base64 în răspuns → ~8 milioane de caractere per poză. Asta:
- depășește limita de tokeni per apel aproape mereu (rezultatul e salvat automat pe disc de harness,
  dar tot consumă timp/tokeni de context ca să gestionezi fiecare notificare de „exceeds maximum
  allowed tokens");
- e lent (transfer de multe MB) și, empiric, **instabil la fișiere mari — apeluri paralele sau chiar
  secvențiale eșuează des cu „MCP server session expired"**, uneori repetat pe același fișier;
- e complet inutil, pentru că GPS-ul stă în EXIF, în primii ~5-65 KB din fișier, nu în restul de 6 MB
  de date de imagine.

**Soluție: `scripts/fetch_gps_fast.py`.** Pozele din acest proiect sunt partajate în Drive ca „oricine
cu linkul poate vizualiza" (verificat — vezi „Decizii deja luate" mai jos). Asta face posibil un simplu
`GET` HTTP cu header `Range` către `https://drive.google.com/uc?export=download&id=<FILE_ID>`, fără
autentificare și fără tool MCP, cerând explicit doar primii 256 KB din fișier (`Range: bytes=0-262143`).
Acei 256 KB conțin sigur segmentul EXIF. Script-ul salvează prefixul într-un fișier temporar și-l
pasează prin `scripts/gps_exif.py` (același parser, neschimbat). **Verificat empiric pe 8 poze**:
coordonatele obținute din prefixul de 256 KB sunt identice, la toate zecimalele, cu cele obținute din
fișierul întreg descărcat prin MCP.

Rezultat: 36 de poze procesate în ~15 secunde total (față de ordinul minutelor/eșecuri repetate pentru
doar 8 poze pe calea MCP), cu un consum de tokeni de context aproape zero (niciun payload mare nu trece
prin conversație — totul se întâmplă în `Bash`/`curl`/Python local).

Utilizare tipică pentru un folder nou de poze:
```python
import sys
sys.path.insert(0, "scripts")
from fetch_gps_fast import fetch_gps

gps = fetch_gps(file_id)   # -> (lat, lon) sau None daca nu are GPS / esueaza dupa 3 incercari
```
sau linie de comandă: `python3 scripts/fetch_gps_fast.py <fileId1> <fileId2> ...`.

**Limitări de reținut:**
- Funcționează doar dacă fișierul e partajat public (permisiune „anyone: reader"). Pentru poze noi
  urcate de utilizator în același folder-părinte, asta pare să fie comportamentul implicit observat
  până acum — dar dacă `fetch_gps_fast.py` întoarce `None`/`FAILED` pentru multe poze deodată,
  verifică mai întâi permisiunile fișierului (`get_file_permissions`) înainte să presupui alt bug.
- **Nu folosi paths absolute care încep cu `/` pentru fișierele temporare de output** dacă rescrii
  vreodată acest script — o primă versiune scria la `/tmp_prefix_N.jpg` (rădăcina filesystem-ului) în
  loc de un folder scriptibil, ceea ce a cauzat 36/36 eșecuri false-negative ("DOWNLOAD FAILED") care
  păreau limitare Google, dar erau doar un bug de path. `fetch_gps_fast.py` folosește deja
  `tempfile.NamedTemporaryFile`, deci problema asta nu ar trebui să mai apară, dar e o lecție utilă
  dacă apare vreodată un simptom similar (eșec brusc, uniform, pe toate fișierele deodată → suspectează
  întâi propriul cod/path, nu neapărat un blocaj extern).

## Decizii deja luate (nu re-întreba, doar aplică)

- **Repo-ul e public, intenționat.** Verificat explicit pe 2026-09-02 (tot istoricul git, toate
  fișierele): niciun token/cheie API/secret, niciun CNP/telefon/IBAN al proprietarului, niciun fișier
  foto original comis. Singura expunere reală e că linkurile Drive din `data.geojson.js` duc la poze
  setate "oricine cu linkul poate vizualiza" — asumat de proprietar, nu semnala ca problemă din nou
  decât dacă apare ceva nou (ex. un fișier cu date personale ajunge din greșeală în repo).
- Mediul de rulare Claude Code (mașină virtuală Debian 13 sub Windows 10) e considerat efemer —
  fișierele locale/scratchpad și memoria locală Claude NU sunt de încredere să persiste între sesiuni.
  **Acest repo (`CLAUDE.md` + `scripts/`) e singura sursă de adevăr persistentă** pentru a relua
  proiectul; orice informație nouă utilă pentru continuare trebuie scrisă aici, nu doar reținută local.

## Notă despre mediul de lucru

Nu presupune că `exiftool`, `Pillow`/`PIL` sau `pip` sunt instalate pe mașina curentă — pe mașina
originală (Linux, fără acces la instalare pachete) niciunul nu era disponibil, de-asta există
`scripts/gps_exif.py` ca fallback fără dependențe. Verifică întâi dacă uneltele native sunt disponibile
(mai rapide/mai robuste), și folosește scriptul din repo doar dacă nu sunt.
