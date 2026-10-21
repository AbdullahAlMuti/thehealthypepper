"""
Create -images junctions for all 90 product folders and verify images.
"""

import os
import subprocess
import json

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRODUCTS_DIR = os.path.join(WORKSPACE_ROOT, "Products")
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
PRODUCTS_JSON = os.path.join(DATA_DIR, "products.json")

def main():
    folders = [d for d in os.listdir(PRODUCTS_DIR) if os.path.isdir(os.path.join(PRODUCTS_DIR, d))]
    print(f"Total product folders found: {len(folders)}")

    junction_count = 0
    total_images = 0
    total_bytes = 0
    zero_bytes = []

    for folder_name in folders:
        folder_path = os.path.join(PRODUCTS_DIR, folder_name)
        images_dir = os.path.join(folder_path, "images")
        dash_images_dir = os.path.join(folder_path, "-images")

        if not os.path.exists(images_dir):
            print(f"[!] Warning: No images dir in {folder_name}")
            continue

        images = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
        total_images += len(images)

        for img in images:
            img_path = os.path.join(images_dir, img)
            sz = os.path.getsize(img_path)
            if sz == 0:
                zero_bytes.append(img_path)
            total_bytes += sz

        # Ensure -images junction exists
        if not os.path.exists(dash_images_dir):
            escaped_dash = dash_images_dir.replace("'", "''")
            escaped_img = images_dir.replace("'", "''")
            ps_cmd = f"New-Item -ItemType Junction -Path '{escaped_dash}' -Target '{escaped_img}'"
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
            if proc.returncode == 0:
                junction_count += 1
            else:
                print(f"[-] Failed to create junction for {folder_name}: {proc.stderr.strip()}")
        else:
            junction_count += 1

    print(f"[+] Total folders: {len(folders)}")
    print(f"[+] Total -images junctions active: {junction_count}/{len(folders)}")
    print(f"[+] Total images: {total_images}")
    print(f"[+] Total media size: {total_bytes / (1024 * 1024):.2f} MB")
    print(f"[+] Zero-byte files: {len(zero_bytes)}")

    if len(folders) == 90 and total_images == 508 and len(zero_bytes) == 0:
        print("\n[SUCCESS] All 90 products and 508 images verified with 100% integrity!")
    else:
        print("\n[FAILURE] Image count or integrity mismatch!")

if __name__ == "__main__":
    main()
