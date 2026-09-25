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

**260917 + 260918 + 260922 + 260923** — toate patru complet procesate (primele trei pe 22 sept 2026,
260923 pe 25 sept 2026), ambele tipuri de poze incluse:
- poze "conota" (`YYYYMMDD_HHMMSS.jpg`): 260917 (56), 260918 (52), 260922 (9), 260923 (9) — pe hartă din
  prima trecere, coordonate din EXIF normal (260923 nu a avut probleme, EXIF valid pe toate 9).
- poze "geofoto"/COPIE (`DD-MM-2026_HH-MM-SS_RO<parcela>_..._COPIE.jpg`, owner `vlgps659@gmail.com`):
  260917 (105), 260918 (105), 260922 (20), 260923 (16) — toate 246 unice pe hartă, coordonate obținute
  prin **citire vizuală a overlay-ului text din imagine** (vezi secțiunea "Metoda de citire vizuală" de
  mai jos) — verificat empiric la fiecare folder (inclusiv 260923) că EXIF e complet zero și nu există
  bloc XMP, deci s-a sărit direct la metoda vizuală. NU s-au găsit duplicate în niciunul din cele patru
  foldere (verificat, 0 titluri repetate per folder) — problema duplicatelor a apărut o singură dată,
  doar în 260917, și a fost rezolvată manual de proprietar în Drive.

Vezi git log pentru istoricul exact al folderelor incluse deja (mesajele de commit sunt de forma
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

## Bug descoperit pe 21 sept 2026: GPS zero in EXIF, coordonate reale in XMP (foldere 260917/260918)

La procesarea 260917/260918, `fetch_gps_fast.py`/`gps_exif.py` întorcea `(0.0, 0.0)` pentru toate pozele,
deși GPS IFD-ul EXIF era prezent (tag-urile GPS existau, structural corecte). Cauza: aplicația foto
(o versiune mai nouă, se pare bazată pe "spotLens"/Conota, telefon Pixel 9a) scrie GPS IFD-ul din EXIF
ca un placeholder cu toate valorile zero (inclusiv `GPSLatitudeRef`/`GPSLongitudeRef` goale), dar scrie
coordonatele *reale* într-un bloc XMP separat (segment JPEG `APP1` cu semnătura `http://ns.adobe.com/xap/1.0/`,
imediat după segmentul Exif), ca atribute zecimale semnate:
`Iptc4xmpExt:GPSLatitude="44.88..."` / `Iptc4xmpExt:GPSLongitude="24.28..."`.

**Fix aplicat în `scripts/gps_exif.py`:** `get_gps()` încearcă întâi parsarea EXIF ca înainte; dacă
rezultatul e `None` sau exact `(0.0, 0.0)`, cade pe un fallback regex simplu peste primii 2 MB ai
fișierului care caută `GPSLatitude="..."` / `GPSLongitude="..."` (funcția `_get_gps_xmp`). Nu s-a schimbat
nimic în `fetch_gps_fast.py` — fallback-ul funcționează automat pe același prefix de 256 KB, fiindcă
blocul XMP e tot lângă începutul fișierului, la fel ca EXIF-ul.

Dacă `fetch_gps_fast.py` întoarce iar `(0.0, 0.0)` sau `None` pentru multe poze deodată pe un folder
viitor, verifică întâi ipoteza asta (EXIF placeholder + XMP cu coordonate reale) înainte să presupui
altă cauză — descarcă un prefix cu `curl -r 0-262143` și caută manual `GPSLatitude=` în el.

## Bug descoperit pe 22 sept 2026: poze COPIE fără GPS recuperabil (nici EXIF, nici XMP)

La procesarea 260917/260918/260922 s-a găsit, în plus față de pozele "conota" obișnuite, un al doilea
set de poze în aceleași foldere: nume `DD-MM-2026_HH-MM-SS_RO<parcela>_..._COPIE.jpg`, owner
`vlgps659@gmail.com` (o unealtă diferită de "conota", probabil de validare parcele APIA — nu telefonul
utilizatorului). Tipul ăsta de nume nu e nou (829 de intrări "COPIE" mai vechi, din august, sunt deja pe
hartă cu coordonate valide), dar **acest batch specific (17/18/22 sept 2026, toate încărcate deodată pe
22 sept ~18:1x-18:26 UTC) are GPS IFD-ul din EXIF complet zero (toți octeții din zona GPS IFD literal
`0x00`, verificat pe fișier întreg, nu doar prefix) și NU are deloc bloc XMP** (spre deosebire de bug-ul
similar din 21 sept, documentat mai jos, unde XMP conținea coordonatele reale) — verificat pe eșantioane
din 260917 și din 260922, descărcând fișierul întreg (~0.8-1.4 MB, deci nu e problemă de prefix/Range).
Rezultat: din 235 de poze COPIE unice (după dedup) găsite în cele 3 foldere, GPS extras a fost `(0.0,
0.0)` pentru toate 235 — tratat ca "fără GPS", sărit de la adăugare pe hartă (nu au fost adăugate cu
coordonate false).

**Dacă apare din nou** (folder viitor cu poze COPIE toate cu GPS zero): verifică întâi dacă e același
fenomen (grep manual după `GPSLatitude=` pe fișierul întreg descărcat — nu doar pe un prefix, ca să
excluzi problema de trunchiere) înainte să presupui alt bug. Momentan pare o problemă la sursă (unealta
`vlgps659`), nu ceva reparabil din partea noastră — nu există GPS recuperabil în EXIF/XMP pentru acest tip
de poze. Dacă la un moment dat poze COPIE noi au din nou GPS valid (ca cele 829 vechi), nu presupune că
bug-ul ăsta persistă pe termen nelimitat — verifică empiric la fiecare folder nou. **Actualizare 22 sept
2026 (reprocesare 260917):** deși EXIF/XMP rămân goale, coordonatele EXISTĂ vizibil ca text suprapus pe
fiecare imagine (aplicația "geofoto" scrie un watermark cu lat/lon direct pe poză) — vezi secțiunea
"Metoda de citire vizuală a coordonatelor GPS" de mai jos. Deci "fără GPS recuperabil" înseamnă doar
"fără GPS recuperabil automat din EXIF/XMP", nu "fără GPS deloc" — verifică întâi vizual (pe un eșantion
de 2-3 poze, deschide imaginea întreagă cu Read) înainte să tratezi un folder COPIE ca fiind cu adevărat
fără coordonate.

**Actualizare 22 sept 2026 (260918+260922):** toate cele 125 poze COPIE unice din aceste două foldere au
avut același tipar (EXIF zero, fără XMP, verificat pe eșantioane) și au fost rezolvate prin metoda vizuală
— vezi „Ultimul folder procesat" de mai sus. Nicio poză COPIE rămasă fără GPS la acest lot.

## Metoda de citire vizuală a coordonatelor GPS (poze "geofoto"/COPIE, folosită pe 260917, 260918, 260922 pe 22 sept 2026)

Aplicația "geofoto" (owner fișiere `vlgps659@gmail.com`) suprapune pe fiecare poză un banner text în
partea de jos a imaginii (fundal semi-transparent negru, text alb), cu formatul (linie cu linie):
```
<cod parcelă>
<cod parcelă>
DD/MM/AAAA HH:MM
<LAT>, <LON>
Altitudine: <n>
 Orientare: <N/S/E/V/...>
Versiune app: <x.y.z> - DD/MM/AAAA
```
Linia a 4-a e coordonatele GPS reale, zecimale semnate, format `lat, lon` (ex. `44.8016237,
24.3419112`), separate de virgulă+spațiu. Verificat pe 3 poze eșantion din 260917: valorile citite
vizual coincid exact cu timestamp-ul din numele fișierului și sunt plauzibile geografic (zona parcelelor
APIA din proiect). Poza are rezoluție tipică 1080×1920 (portret); banner-ul ocupă aproximativ ultimii
22% din înălțime (`y` de la `0.78*H` la `H`), iar linia de coordonate e la aproximativ `0.335`–`0.44`
din înălțimea acelui banner (deci `y` absolut ≈ `0.855*H`–`0.87*H`) — utilă ca reper pentru crop automat
dacă se repetă la un folder viitor, dar verifică empiric, poate varia cu versiunea aplicației
(`Versiune app` apărea `4.1.1 - 05/08/2026` pe eșantioanele verificate).

**Flux folosit pentru procesarea în masă a 105 poze (eficient, fără să citească 105 imagini întregi):**
1. Descarcă fiecare poză *întreagă* (nu doar prefixul de 256 KB — banner-ul e la finalul fișierului,
   dincolo de zona EXIF) direct prin `curl` pe link-ul public (`https://drive.google.com/uc?export=download&id=<FILE_ID>`,
   fără Range) — NU prin tool-ul MCP `download_file_content` (poze de ~1-1.4 MB fiecare tot depășesc
   limita de tokeni per apel a MCP-ului quando codate base64; curl direct e gratuit ca tokeni și mult
   mai rapid).
2. Cu Pillow (`pip install pillow` — a funcționat pe mașina folosită la această sesiune, deși nu era
   instalat implicit; vezi nota generală despre mediu mai jos) decupează doar linia de coordonate din
   fiecare poză (banda îngustă descrisă mai sus), apoi asamblează un "grid" compus din mai multe poze
   (10-15) stivuite vertical într-o singură imagine JPEG, cu un index numeric desenat lângă fiecare
   linie (`ImageDraw` + `DejaVuSans-Bold.ttf`, disponibil implicit în `/usr/share/fonts/truetype/dejavu/`).
3. Citește (tool `Read`, vizual) fiecare imagine-compus (nu poza originală) — reduce numărul de citiri
   de la 105 la ~9, cu text perfect lizibil la lățime completă (1080px). Verifică acuratețea pe minim 3
   eșantioane comparând cu citirea manuală a pozei întregi înainte de a te baza pe pipeline pe tot lotul
   (verificat pe acest folder: 3/3 eșantioane identice).
4. Notează indexul din grid → mapează înapoi la `file_id`/`title` printr-un tabel index→id salvat
   separat (ordine deterministă, ex. sortată după `title`).

Această metodă a fost necesară fiindcă EXIF/XMP nu conțin coordonate pentru acest lot (vezi bug de mai
sus) — dacă un folder viitor are din nou EXIF/XMP goale pentru poze COPIE, verifică întâi dacă banner-ul
vizual există (poate lipsi la alte versiuni de app) înainte de a presupune că se aplică aceeași soluție.

**Capcană găsită la refolosirea pipeline-ului (260918/260922, 22 sept 2026):** dacă desenezi eticheta
index deasupra fiecărei linii cu `ImageDraw.text`, folosește poziția `y` curentă din bucla de asamblare
(`draw.text((5, y+3), ...)`), NU o constantă fixă (`draw.text((5, 3), ...)`) — altfel toate etichetele se
suprapun la începutul imaginii-grid (garbled) în loc să apară fiecare deasupra rândului ei. Nu afectează
coordonatele citite (crop-urile în sine sunt poziționate corect independent de etichetă), dar face
etichetele ilizibile — verifică vizual primul grid generat înainte de a continua cu restul lotului.

## Limitare descoperită pe 22 sept 2026: nu se pot trash-ui fișiere Drive ale altui cont (owner diferit)

La folderele 260917/260918/260922 s-au găsit poze COPIE duplicate exact (același titlu, ID-uri Drive
diferite) — 104 duplicate doar în 260917 (fiecare din cele 110 poze unice era încărcată de 2 ori, cu
excepția a 6 care aveau o singură copie). Am încercat să le trash-uim cu tool-ul MCP `trash_file`, dar
**toate apelurile au eșuat cu "The caller does not have permission"**, deși `nic.mol@gmail.com` (contul
autentificat pe MCP) e OWNER pe folderul 260917 însuși. Cauza: fișierele COPIE sunt deținute de un cont
diferit (`vlgps659@gmail.com`), iar `get_file_permissions` pe unul dintre ele arată doar
`owner: vlgps659@gmail.com` și `anyone: reader` — nici o permisiune explicită pentru `nic.mol`. Testat
și alternative: `update_file` cu `title` nou (rename) **funcționează** (deci există un anumit acces de
scriere pe metadate), dar `update_file` cu `parentId` nou (mutare în alt folder) **eșuează la fel** cu
"permission" — deci nu există nicio cale prin API-ul MCP disponibil de a scoate/șterge fișierele astea
din folder. (Am verificat că `trash_file` funcționează normal pe fișiere/foldere deținute chiar de
`nic.mol` — deci nu e un bug general al tool-ului.)

**Concluzie practică:** dacă apar iar duplicate în poze COPIE (owner `vlgps659` sau alt cont diferit de
`nic.mol`), NU presupune că le poți trash-ui automat — testează întâi cu un singur fișier; dacă eșuează
la fel, sari peste pasul de ștergere efectivă din Drive, dar tot exclude duplicatele din `data.geojson.js`
(păstrează o singură intrare per titlu unic, cea cu `createdTime` mai vechi) ca să nu apară puncte
duplicate pe hartă. Raportează utilizatorului lista exactă de ID-uri duplicate găsite, ca să le poată
șterge manual din Drive (ca owner al contului `vlgps659`, sau cerând owner-ului acelui cont s-o facă) —
UI-ul web Drive ar putea permite acțiuni pe care API-ul (cu scope-ul curent) nu le permite, deci merită
încercat manual înainte de a presupune că ștergerea e complet imposibilă.

**Actualizare 22 sept 2026 (reverificare 260917):** utilizatorul a confirmat că a rezolvat manual
problema (probabil șters/reîncărcat prin UI-ul web Drive, cont `vlgps659`). La reverificarea completă a
folderului 260917 (toate paginile, 161 fișiere unice), cele 104 perechi de duplicate documentate mai sus
NU mai existau — exact 105 titluri COPIE, fiecare cu un singur ID Drive (ID-uri noi, `createdTime` de pe
22 sept ~19:32 UTC, diferite de cele vechi listate mai sus care nu mai există în folder). Deci limitarea
API-ului MCP (nu poți trash-ui fișiere ale altui owner) rămâne valabilă ca fapt tehnic, dar nu mai e un
blocaj practic pentru acest folder — utilizatorul a putut rezolva pe altă cale. Nu presupune că e rezolvat
și pentru 260918/260922 (neverificate la această sesiune) sau pentru foldere viitoare.

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
