#
# Living Notitia
# combine_sources.py
#

from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

OCCIDENTIS=ROOT/"data"/"Notitia_OCC.txt"
ORIENS=ROOT/"data"/"Notitia_oriens.txt"
OUTPUT=ROOT/"data"/"Notitia.txt"

with open(
    OCCIDENTIS,
    encoding="utf-8"
) as f:
    occidentis=f.read().rstrip()

with open(
    ORIENS,
    encoding="utf-8"
) as f:
    oriens=f.read().rstrip()

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    f.write("DOCUMENT: Occidentis\n\n")
    f.write(occidentis)
    f.write("\n\n")
    f.write("DOCUMENT: Oriens\n\n")
    f.write(oriens)
    f.write("\n")

print()
print("Living Notitia")
print("combine_sources.py")
print()
print("Occidentis :",OCCIDENTIS)
print("Oriens     :",ORIENS)
print("Output     :",OUTPUT)
print()