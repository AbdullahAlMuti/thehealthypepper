"""
Reorganize Products folder to structure by Product Name:
Products/
  <Product Name>/
    images/
      image_01.jpg
      ...
    -images/ (junction to images/)
    description.html
    metadata.json
"""

import os
import sys
import json
import subprocess
import shutil
import urllib.parse
import requests

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRODUCTS_DIR = os.path.join(WORKSPACE_ROOT, "Products")
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
PRODUCTS_JSON = os.path.join(DATA_DIR, "products.json")

def sanitize_folder_name(name: str) -> str:
    # Windows forbidden characters: \ / : * ? " < > |
    forbidden = r'\/:*?"<>|'
    clean = "".join("-" if c in forbidden else c for c in name).strip()
    return clean

def main():
    if not os.path.exists(PRODUCTS_JSON):
        print(f"[-] Missing {PRODUCTS_JSON}", file=sys.stderr)
        sys.exit(1)

    with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
        products = json.load(f)["products"]

    print(f"[*] Reorganizing {len(products)} products into Products/<Product Name>/images...")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    # Read existing products folders in Products/
    existing_folders = {d.lower(): d for d in os.listdir(PRODUCTS_DIR) if os.path.isdir(os.path.join(PRODUCTS_DIR, d))}

    for idx, p in enumerate(products, 1):
        title = p["title"].strip()
        handle = (p.get("handle") or "").strip()
        folder_name = sanitize_folder_name(title)
        target_dir = os.path.join(PRODUCTS_DIR, folder_name)
        target_images_dir = os.path.join(target_dir, "images")

        # Temporary source if handle folder exists
        source_handle_dir = None
        if handle.lower() in existing_folders:
            source_handle_dir = os.path.join(PRODUCTS_DIR, existing_folders[handle.lower()])

        os.makedirs(target_images_dir, exist_ok=True)

        # 1. Move or download images
        images = p.get("images", []) or []
        for img_idx, img in enumerate(images, 1):
            src = img.get("src", "")
            clean_url = src.split("?")[0]
            parsed_path = urllib.parse.urlparse(clean_url).path
            _, ext = os.path.splitext(parsed_path)
            if not ext or len(ext) > 5:
                ext = ".jpg"
            img_filename = f"image_{img_idx:02d}{ext.lower()}"
            target_img_path = os.path.join(target_images_dir, img_filename)

            # Check if source exists in source_handle_dir
            if source_handle_dir and source_handle_dir.lower() != target_dir.lower():
                source_img_path = os.path.join(source_handle_dir, "images", img_filename)
                if os.path.exists(source_img_path) and os.path.getsize(source_img_path) > 0:
                    if not os.path.exists(target_img_path) or os.path.getsize(target_img_path) == 0:
                        shutil.copy2(source_img_path, target_img_path)

            # If still missing or 0 bytes, download it directly
            if not os.path.exists(target_img_path) or os.path.getsize(target_img_path) == 0:
                print(f"    Downloading missing image {img_filename} for {title}...")
                resp = session.get(clean_url, timeout=20)
                if resp.status_code == 200:
                    with open(target_img_path, "wb") as f:
                        f.write(resp.content)

        # 2. metadata.json
        meta_path = os.path.join(target_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(p, f, indent=2, ensure_ascii=False)

        # 3. description.html
        desc_path = os.path.join(target_dir, "description.html")
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(p.get("body_html") or "")

        # 4. Create -images junction inside target_dir
        dash_images_path = os.path.join(target_dir, "-images")
        if not os.path.exists(dash_images_path):
            try:
                # cmd /c mklink /J "<dash_images_path>" "<target_images_dir>"
                subprocess.run(
                    ["cmd", "/c", f'mklink /J "{dash_images_path}" "{target_images_dir}"'],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"[-] Could not create junction for {dash_images_path}: {e}")

        # If source_handle_dir is completely different from target_dir, remove old handle folder
        if source_handle_dir and source_handle_dir.lower() != target_dir.lower():
            try:
                shutil.rmtree(source_handle_dir)
            except Exception as e:
                print(f"[-] Warning: could not remove old folder {source_handle_dir}: {e}")
        elif source_handle_dir and os.path.basename(source_handle_dir) != os.path.basename(target_dir):
            # Same folder case-insensitively, fix case on disk
            try:
                temp_case = target_dir + "_case_rename"
                os.rename(source_handle_dir, temp_case)
                os.rename(temp_case, target_dir)
            except Exception as e:
                pass

        if idx % 15 == 0 or idx == len(products):
            print(f"    Processed {idx}/{len(products)} products...")

    print("[+] Organization complete!")

if __name__ == "__main__":
    main()
