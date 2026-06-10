#!/usr/bin/env python3
"""
Sostituzione foto in un VdS iliad COLOC preservando l'aspect ratio dello slot
del template, per evitare le immagini "stirate".

Strategia:
  - Legge cx/cy in EMU dai drawing del documento (wp:extent + pic:spPr/a:xfrm/a:ext)
  - Confronta con aspect ratio della foto sorgente
  - Se differiscono > 5%: pad bianco con Pillow.ImageOps.pad per matchare slot
  - Altrimenti: salva direttamente preservando formato slot (PNG/JPEG)
  - Output ottimizzato: max 1600px lato lungo, JPEG q=85, PNG optimize=True

Uso:
    python swap_photos.py <docx_path> <photo1> <photo2> ... <photoN>

dove photoN sono i file in ordine di slot (1..N). Slot esistenti nel template:
quelli usati nel master VdS iliad COLOC = 14.
"""
import os, sys, shutil, zipfile, re
from PIL import Image, ImageOps

EMU_PER_INCH = 914400

def list_slots(unpacked_dir):
    """Ritorna lista di tuple (media_filename, cx, cy) nell'ordine di apparizione del documento."""
    doc_xml = open(f"{unpacked_dir}/word/document.xml").read()
    rels_xml = open(f"{unpacked_dir}/word/_rels/document.xml.rels").read()
    # rId -> Target
    rid_to_target = dict(re.findall(r'Id="(rId\d+)"[^/]*Target="(media/[^"]+)"', rels_xml))
    # Trova drawings: wp:extent cx="..." cy="..." + r:embed
    pattern = re.compile(
        r'<wp:extent\s+cx="(\d+)"\s+cy="(\d+)"/>.*?r:embed="(rId\d+)"',
        re.DOTALL
    )
    slots = []
    for m in pattern.finditer(doc_xml):
        cx, cy, rid = int(m.group(1)), int(m.group(2)), m.group(3)
        target = rid_to_target.get(rid)
        if target:
            slots.append((target, cx, cy))
    return slots

def fit_photo_to_slot(src_path, target_path, slot_cx_emu, slot_cy_emu, max_px=1600):
    """Salva la foto adattandola all'aspect ratio dello slot, padding bianco se serve."""
    img = Image.open(src_path)
    # Correggi orientamento EXIF (foto smartphone)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    slot_ar = slot_cx_emu / slot_cy_emu
    img_ar = img.size[0] / img.size[1]
    diff_pct = abs(slot_ar - img_ar) / slot_ar * 100

    if diff_pct > 5:
        # Pad per matchare aspect dello slot
        # Calcola dimensione finale: max_px sul lato lungo dello slot, mantenendo slot_ar
        if slot_ar >= 1:  # landscape
            out_w = max_px
            out_h = int(max_px / slot_ar)
        else:             # portrait
            out_h = max_px
            out_w = int(max_px * slot_ar)
        # ImageOps.pad: ridimensiona preservando aspect originale + pad bianco al target
        img_padded = ImageOps.pad(img, (out_w, out_h), color=(255,255,255), method=Image.LANCZOS)
        img_out = img_padded
    else:
        # Aspect compatibile: solo resize
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        img_out = img

    ext = os.path.splitext(target_path)[1].lower().lstrip('.')
    if ext == "png":
        img_out.save(target_path, "PNG", optimize=True)
    else:
        img_out.save(target_path, "JPEG", quality=85, optimize=True)
    return img_out.size, diff_pct > 5

def swap(docx_path, photos):
    work = "/tmp/_vds_swap"
    if os.path.exists(work):
        shutil.rmtree(work)
    with zipfile.ZipFile(docx_path) as z:
        z.extractall(work)
    slots = list_slots(work)
    if len(slots) != len(photos):
        print(f"WARNING: slot trovati {len(slots)}, foto fornite {len(photos)}", file=sys.stderr)
    report = []
    for i, ((media, cx, cy), photo) in enumerate(zip(slots, photos), 1):
        if not photo or not os.path.exists(photo):
            report.append(f"  slot {i}: SKIP ({media}) — foto non fornita/inesistente")
            continue
        target = f"{work}/word/{media}"
        size, padded = fit_photo_to_slot(photo, target, cx, cy)
        report.append(f"  slot {i}: {os.path.basename(photo)} -> {media}  size={size}  padded={padded}")
    # Repack
    if os.path.exists(docx_path):
        os.remove(docx_path)
    with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(work):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, work)
                z.write(full, arc)
    return report

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    docx = sys.argv[1]
    photos = sys.argv[2:]
    report = swap(docx, photos)
    print("\n".join(report))
    print(f"\nOK -> {docx}")
