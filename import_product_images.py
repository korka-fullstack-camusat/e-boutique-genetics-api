"""
Import en masse des photos produits.

Les photos sont nommées d'après l'id du produit : produit-<id>.png / .jpg / .jpeg / .webp
Chaque photo est redimensionnée (1600 px max), convertie en WebP et copiée dans
uploads/produits/, puis devient la photo principale du produit en base.
Les anciennes listes d'images sont sauvegardées dans uploads/anciennes-images.json
(seulement à la première sauvegarde de chaque produit) pour pouvoir revenir en arrière.

Usage :
    python import_product_images.py DOSSIER_PHOTOS            # aperçu, ne modifie rien
    python import_product_images.py DOSSIER_PHOTOS --apply    # applique
"""
import json
import os
import re
import sys
from pathlib import Path

import psycopg
from psycopg.types.json import Json
from dotenv import load_dotenv
from PIL import Image, ImageOps

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads" / "produits"
BACKUP_FILE = BASE_DIR / "uploads" / "anciennes-images.json"
URL_PREFIX = "/uploads/produits/"
MAX_DIM = 1600
FILE_RE = re.compile(r"^produit-(\d+)\.(png|jpe?g|webp)$", re.IGNORECASE)
# Liens vers l'ancien serveur, hors ligne : remplacés par la nouvelle photo
DEAD_PREFIXES = ("https://genetics-market.com/uploads/", "http://genetics-market.com/uploads/")


def db_url() -> str:
    raw = re.sub(r"\?.*$", "", os.getenv("DATABASE_URL", ""))
    return raw + "?sslmode=require"


def convert(src: Path, dest: Path) -> None:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        im.thumbnail((MAX_DIM, MAX_DIM))
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        im.save(dest, "WEBP", quality=85, method=6)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    apply = "--apply" in sys.argv

    photos = {}
    for f in sorted(folder.iterdir()):
        m = FILE_RE.match(f.name)
        if m:
            photos[int(m.group(1))] = f
        elif f.is_file() and not f.name.startswith("."):
            print(f"  ignoré (nom non reconnu) : {f.name}")

    with psycopg.connect(db_url()) as conn:
        rows = conn.execute("SELECT id, name, images FROM products WHERE id = ANY(%s)", (list(photos),)).fetchall()
        products = {r[0]: (r[1], r[2] or []) for r in rows}

        unknown = sorted(set(photos) - set(products))
        for pid in unknown:
            print(f"  ignoré (aucun produit avec l'id {pid}) : {photos[pid].name}")

        backup = json.loads(BACKUP_FILE.read_text()) if BACKUP_FILE.exists() else {}
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        for pid in sorted(set(photos) & set(products)):
            name, images = products[pid]
            new_url = f"{URL_PREFIX}produit-{pid}.webp"
            kept = [u for u in images if not u.startswith(DEAD_PREFIXES) and u != new_url]
            new_images = [new_url] + kept
            print(f"  [{pid}] {name} : {images} -> {new_images}")
            if not apply:
                continue
            convert(photos[pid], UPLOAD_DIR / f"produit-{pid}.webp")
            backup.setdefault(str(pid), images)
            conn.execute("UPDATE products SET images = %s WHERE id = %s", (Json(new_images), pid))

        if apply:
            BACKUP_FILE.write_text(json.dumps(backup, ensure_ascii=False, indent=2))
            conn.commit()

    count = len(set(photos) & set(products))
    print(f"\n{count} produit(s) {'mis à jour' if apply else 'à mettre à jour (aperçu, rien modifié — ajoutez --apply)'}")


if __name__ == "__main__":
    main()
