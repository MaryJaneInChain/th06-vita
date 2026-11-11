"""Rewrite a VPK (a zip) with fixed timestamps and permissions, so the same contents always give the same bytes.
vita-pack-vpk stores each file's mtime in local time. Usage: normalize_vpk.py FILE.vpk"""
import os
import sys
import zipfile

path = sys.argv[1]
with zipfile.ZipFile(path) as src:
    entries = [(info, src.read(info)) for info in src.infolist()]
with zipfile.ZipFile(path + ".tmp", "w") as dst:
    for info, data in entries:
        fixed = zipfile.ZipInfo(info.filename, date_time=(1980, 1, 1, 0, 0, 0))
        fixed.compress_type = info.compress_type
        fixed.create_system = 3
        fixed.external_attr = (0o40755 if info.is_dir() else 0o100644) << 16
        dst.writestr(fixed, data)
os.replace(path + ".tmp", path)
