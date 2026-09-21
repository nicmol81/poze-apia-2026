#!/usr/bin/env python3
"""Minimal pure-python EXIF GPS extractor (no external deps)."""
import re
import struct
import sys

# Unele poze (Conota/spotLens, vazut prima data pe 260917/260918) scriu un GPS IFD
# in EXIF cu toate valorile zero (placeholder nescris corect), dar coordonatele
# reale sunt prezente in blocul XMP alaturat, ca atribute decimale semnate:
# Iptc4xmpExt:GPSLatitude="44.88..." Iptc4xmpExt:GPSLongitude="24.28...".
# Fallback-ul de mai jos citeste XMP-ul cand EXIF-ul lipseste sau e (0.0, 0.0).
_XMP_LAT_RE = re.compile(rb'GPSLatitude="(-?[0-9.]+)"')
_XMP_LON_RE = re.compile(rb'GPSLongitude="(-?[0-9.]+)"')


def _get_gps_xmp(data):
    m_lat = _XMP_LAT_RE.search(data)
    m_lon = _XMP_LON_RE.search(data)
    if not m_lat or not m_lon:
        return None
    return float(m_lat.group(1)), float(m_lon.group(1))

TYPE_SIZES = {1:1, 2:1, 3:2, 4:4, 5:8, 6:1, 7:1, 8:2, 9:4, 10:8, 11:4, 12:8}

def read_ifd(data, tiff_start, offset, endian):
    entries = {}
    (count,) = struct.unpack_from(endian + 'H', data, offset)
    p = offset + 2
    for _ in range(count):
        tag, typ, cnt = struct.unpack_from(endian + 'HHI', data, p)
        size = TYPE_SIZES.get(typ, 1) * cnt
        val_off = p + 8
        if size > 4:
            (val_off,) = struct.unpack_from(endian + 'I', data, p + 8)
            val_off += tiff_start
        entries[tag] = (typ, cnt, val_off)
        p += 12
    (next_ifd,) = struct.unpack_from(endian + 'I', data, p)
    return entries, next_ifd

def read_rationals(data, typ, cnt, off, endian):
    fmt = 'i' if typ == 10 else 'I'
    vals = []
    for i in range(cnt):
        num, den = struct.unpack_from(endian + fmt + fmt, data, off + i * 8)
        vals.append(num / den if den else 0)
    return vals

def read_ascii(data, cnt, off):
    return data[off:off + cnt].split(b'\x00')[0].decode('ascii', 'replace')

def _get_gps_exif(data):
    if data[0:2] != b'\xff\xd8':
        return None
    p = 2
    exif_data = None
    while p < len(data) - 4:
        if data[p] != 0xFF:
            break
        marker = data[p + 1]
        if marker in (0xD8, 0xD9):
            p += 2
            continue
        seg_len = struct.unpack_from('>H', data, p + 2)[0]
        if marker == 0xE1 and data[p + 4:p + 10] == b'Exif\x00\x00':
            exif_data = data[p + 10:p + 2 + seg_len]
            break
        p += 2 + seg_len
    if exif_data is None:
        return None

    endian = '<' if exif_data[0:2] == b'II' else '>'
    (ifd0_off,) = struct.unpack_from(endian + 'I', exif_data, 4)
    ifd0, _ = read_ifd(exif_data, 0, ifd0_off, endian)

    GPS_TAG = 0x8825
    if GPS_TAG not in ifd0:
        return None
    _, _, gps_ptr_loc = ifd0[GPS_TAG]
    # tag value is a LONG stored inline (size 4) -> gps_ptr_loc points at the
    # 4 bytes holding the actual offset to the GPS IFD.
    (gps_off,) = struct.unpack_from(endian + 'I', exif_data, gps_ptr_loc)
    gps_ifd, _ = read_ifd(exif_data, 0, gps_off, endian)

    def dms_to_deg(vals, ref):
        deg = vals[0] + vals[1] / 60 + vals[2] / 3600
        if ref in (b'S', b'W', 'S', 'W'):
            deg = -deg
        return deg

    if 1 not in gps_ifd or 2 not in gps_ifd or 3 not in gps_ifd or 4 not in gps_ifd:
        return None

    lat_ref_t, lat_ref_c, lat_ref_o = gps_ifd[1]
    lat_ref = read_ascii(exif_data, lat_ref_c, lat_ref_o) if lat_ref_c > 4 else exif_data[lat_ref_o:lat_ref_o+1].decode()
    lat_t, lat_c, lat_o = gps_ifd[2]
    lat_vals = read_rationals(exif_data, lat_t, lat_c, lat_o, endian)

    lon_ref_t, lon_ref_c, lon_ref_o = gps_ifd[3]
    lon_ref = read_ascii(exif_data, lon_ref_c, lon_ref_o) if lon_ref_c > 4 else exif_data[lon_ref_o:lon_ref_o+1].decode()
    lon_t, lon_c, lon_o = gps_ifd[4]
    lon_vals = read_rationals(exif_data, lon_t, lon_c, lon_o, endian)

    lat = dms_to_deg(lat_vals, lat_ref)
    lon = dms_to_deg(lon_vals, lon_ref)
    return lat, lon


def get_gps(path):
    with open(path, 'rb') as f:
        data = f.read(2 * 1024 * 1024)  # EXIF/XMP sunt aproape de inceputul fisierului
    result = _get_gps_exif(data)
    if result is None or result == (0.0, 0.0):
        xmp_result = _get_gps_xmp(data)
        if xmp_result is not None:
            return xmp_result
    return result

if __name__ == '__main__':
    for path in sys.argv[1:]:
        r = get_gps(path)
        print(path, r)
