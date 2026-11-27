"""Bangun dataset deteksi 'person' dari COCO val2017 (tanpa API key).

Mengunduh gambar + anotasi resmi COCO, memfilter anotasi kelas 'person',
lalu menuliskannya ke format YOLO siap latih.

Contoh:
    uv run python scripts/build_person_dataset.py --out dataset/person --limit 2000
"""
import argparse
import json
import os
import random
import shutil
import urllib.request
import zipfile

IMG_URL = "http://images.cocodataset.org/zips/val2017.zip"
ANN_URL = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"


def download(url, dest, label):
    if os.path.exists(dest):
        print(f"  sudah ada: {dest}")
        return dest
    print(f"  mengunduh {label} ...")
    tmp = dest + ".part"
    last = [-1]

    def hook(block, block_size, total):
        if total > 0:
            pct = min(100, block * block_size * 100 // total)
            if pct // 5 != last[0] // 5:
                last[0] = pct
                print(f"    {label}: {pct}%", flush=True)

    urllib.request.urlretrieve(url, tmp, reporthook=hook)
    os.replace(tmp, dest)
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="build/coco")
    ap.add_argument("--out", default="dataset/person")
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--limit", type=int, default=0, help="0 = semua gambar ber-orang")
    ap.add_argument("--neg-frac", type=float, default=0.10,
                    help="proporsi gambar latar tanpa orang (mengurangi false positive)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.root, exist_ok=True)

    img_zip = download(IMG_URL, os.path.join(args.root, "val2017.zip"),
                       "gambar COCO val2017 (~778 MB)")
    ann_zip = download(ANN_URL, os.path.join(args.root, "annotations.zip"),
                       "anotasi COCO (~241 MB)")

    img_dir = os.path.join(args.root, "val2017")
    if not os.path.isdir(img_dir):
        print("  ekstrak gambar ...")
        with zipfile.ZipFile(img_zip) as z:
            z.extractall(args.root)

    ann_path = os.path.join(args.root, "annotations", "instances_val2017.json")
    if not os.path.exists(ann_path):
        print("  ekstrak anotasi ...")
        with zipfile.ZipFile(ann_zip) as z:
            for member in z.namelist():
                if member == "annotations/instances_val2017.json":
                    z.extract(member, args.root)

    print("  baca anotasi ...")
    with open(ann_path, encoding="utf-8") as f:
        coco = json.load(f)

    cats = {c["id"]: c["name"] for c in coco["categories"]}
    person_ids = {cid for cid, name in cats.items() if name == "person"}
    images = {im["id"]: im for im in coco["images"]}

    by_img = {}
    for a in coco["annotations"]:
        if a["category_id"] in person_ids and not a.get("iscrowd", 0):
            by_img.setdefault(a["image_id"], []).append(a)

    pos_ids = list(by_img.keys())
    neg_ids = [i for i in images if i not in by_img]
    random.seed(args.seed)
    random.shuffle(pos_ids)
    random.shuffle(neg_ids)

    n_neg = int(len(pos_ids) * args.neg_frac)
    chosen = pos_ids + neg_ids[:n_neg]
    random.shuffle(chosen)
    if args.limit:
        chosen = chosen[:args.limit]

    if not chosen:
        raise SystemExit("Tidak ada gambar terpilih")

    n_val = max(1, int(len(chosen) * args.val_frac))
    splits = {"val": chosen[:n_val], "train": chosen[n_val:]}

    for split, ids in splits.items():
        img_out = os.path.join(args.out, "images", split)
        lbl_out = os.path.join(args.out, "labels", split)
        os.makedirs(img_out, exist_ok=True)
        os.makedirs(lbl_out, exist_ok=True)

        written = 0
        for iid in ids:
            im = images[iid]
            src = os.path.join(img_dir, im["file_name"])
            if not os.path.exists(src):
                continue
            w, h = im["width"], im["height"]
            shutil.copy2(src, os.path.join(img_out, im["file_name"]))
            stem = os.path.splitext(im["file_name"])[0]
            with open(os.path.join(lbl_out, stem + ".txt"), "w", encoding="utf-8") as fo:
                for a in by_img.get(iid, []):
                    x, y, bw, bh = a["bbox"]
                    cx = (x + bw / 2) / w
                    cy = (y + bh / 2) / h
                    fo.write(f"0 {cx:.6f} {cy:.6f} {bw / w:.6f} {bh / h:.6f}\n")
            written += 1
        print(f"  {split}: {written} gambar")

    data_yaml = os.path.abspath(os.path.join(args.out, "data.yaml"))
    with open(data_yaml, "w", encoding="utf-8") as f:
        f.write(f"path: {os.path.abspath(args.out)}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n\n")
        f.write("names:\n  0: person\n")

    print("Selesai. data.yaml:", data_yaml)


if __name__ == "__main__":
    main()
