#!/usr/bin/env python3
"""Extrage coordonate GPS din poze publice de pe Google Drive FARA sa downloadeze
fisierul intreg si FARA tool-ul MCP Drive (care e lent: incarca tot fisierul,
il codeaza base64 -> milioane de caractere, si expira des la fisiere mari).

Cum functioneaza: EXIF-ul (inclusiv GPS) sta in primii cativa KB dintr-un JPEG.
Fiindca fotografiile din acest proiect sunt partajate "oricine cu linkul poate
vizualiza", putem cere direct prin HTTP doar un prefix din fisier (header
Range), fara autentificare, fara tool MCP. Verificat: coordonatele obtinute
asa sunt IDENTICE cu cele obtinute prin descarcarea completa a fisierului.

Cerinta: fisierul trebuie sa fie partajat public ("anyone: reader") in Drive -
asa sunt toate pozele din acest proiect (verifica cu get_file_permissions daca
ai dubii pe un folder nou).

Utilizare CLI:
    python3 scripts/fetch_gps_fast.py <fileId1> <fileId2> ...
    -> printeaza "<fileId> lat lon" sau "<fileId> NO_GPS" / "<fileId> FAILED"

Utilizare ca modul (recomandat pentru procesare in bulk, vezi CLAUDE.md):
    from scripts.fetch_gps_fast import fetch_gps
    lat, lon = fetch_gps(file_id)  # None daca nu are GPS in EXIF
"""
import subprocess
import sys
import time
import tempfile
import os

from gps_exif import get_gps

# 256 KB e suficient in toate cazurile observate (EXIF-ul e primul segment
# dupa SOI, de regula sub 5 KB; XMP-ul care il urmeaza poate ajunge la ~65 KB
# per segment JPEG - maximul teoretic al unui segment). Marja generoasa.
RANGE_BYTES = "0-262143"


def fetch_gps(file_id, retries=3):
    """Descarca doar prefixul unei poze publice din Drive si extrage (lat, lon).
    Intoarce None daca poza nu are GPS in EXIF sau daca descarcarea esueaza
    dupa `retries` incercari."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        for attempt in range(retries):
            r = subprocess.run(
                ["curl", "-sS", "-r", RANGE_BYTES, "-L", "-o", tmp_path, url],
                capture_output=True, timeout=30,
            )
            if r.returncode == 0 and os.path.getsize(tmp_path) > 0:
                break
            time.sleep(1)
        else:
            return None
        return get_gps(tmp_path)
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    for fid in sys.argv[1:]:
        gps = fetch_gps(fid)
        if gps is None:
            print(f"{fid} NO_GPS_OR_FAILED")
        else:
            lat, lon = gps
            print(f"{fid} {lat} {lon}")
