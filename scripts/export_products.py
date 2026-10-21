"""
The Healthy Pepper Product Export & Archive Tool
Extracts all products, metadata, descriptions, images, and generates a Shopify-compatible CSV.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import requests

from scripts.shopify_formatter import sanitize_handle, format_shopify_csv, extract_product_summary

BASE_URL = "https://thehealthypepper.com/products.json"
MAX_WORKERS = 8
REQUEST_TIMEOUT = 25
MAX_RETRIES = 3


def fetch_all_products(base_url: str = BASE_URL) -> List[Dict[str, Any]]:
    """Fetch all products across pages from Shopify storefront API."""
    all_products = []
    page = 1
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    print(f"[*] Starting product retrieval from {base_url}...", flush=True)
    while True:
        url = f"{base_url}?limit=250&page={page}"
        print(f"    Fetching page {page}: {url}", flush=True)
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            products = data.get("products", [])
            if not products:
                print(f"    No more products found on page {page}.", flush=True)
                break
            all_products.extend(products)
            print(f"    Page {page}: retrieved {len(products)} products (cumulative: {len(all_products)})", flush=True)
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"[-] Error fetching page {page}: {e}", file=sys.stderr, flush=True)
            break

    return all_products


def download_single_image(img_url: str, dest_path: str, retries: int = MAX_RETRIES) -> bool:
    """Download a single image file with retries and size validation."""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return True  # Already exists and is valid

    clean_url = img_url.split("?")[0]
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    for attempt in range(1, retries + 1):
        try:
            r = session.get(clean_url, stream=True, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                if os.path.getsize(dest_path) > 0:
                    return True
                else:
                    os.remove(dest_path)
            time.sleep(attempt * 0.75)
        except Exception as ex:
            if attempt == retries:
                print(f"    [!] Failed to download {clean_url}: {ex}", file=sys.stderr)
            time.sleep(attempt * 1.0)
    return False


def export_catalog(workspace_root: str):
    """Main export pipeline."""
    data_dir = os.path.join(workspace_root, "data")
    products_dir = os.path.join(workspace_root, "products")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(products_dir, exist_ok=True)

    products = fetch_all_products()
    print(f"\n[+] Total products fetched: {len(products)}")

    if not products:
        print("[-] Error: No products fetched. Aborting.", file=sys.stderr)
        return False

    # 1. Save raw products.json
    raw_json_path = os.path.join(data_dir, "products.json")
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump({"products": products}, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved raw JSON to {raw_json_path}")

    # 2. Save products summary
    summary = extract_product_summary(products)
    summary_path = os.path.join(data_dir, "products_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved summary to {summary_path}")

    # 3. Format Shopify CSV
    csv_path = os.path.join(data_dir, "shopify_products_import.csv")
    csv_rows = format_shopify_csv(products, csv_path)
    print(f"[+] Generated Shopify Import CSV ({csv_rows} rows) at {csv_path}")

    # 4. Create individual product directories & collect image download tasks
    download_tasks = []
    print(f"\n[*] Creating individual product archives in {products_dir}...")

    for idx, p in enumerate(products, 1):
        handle = p.get("handle") or f"product-{p.get('id', idx)}"
        sanitized = sanitize_handle(handle)
        prod_folder = os.path.join(products_dir, sanitized)
        os.makedirs(prod_folder, exist_ok=True)

        # metadata.json
        meta_path = os.path.join(prod_folder, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(p, f, indent=2, ensure_ascii=False)

        # description.html
        desc_path = os.path.join(prod_folder, "description.html")
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(p.get("body_html") or "")

        # Queue images
        images = p.get("images", []) or []
        img_dir = os.path.join(prod_folder, "images")
        os.makedirs(img_dir, exist_ok=True)

        for img_idx, img in enumerate(images, 1):
            src = img.get("src")
            if not src:
                continue
            clean_url = src.split("?")[0]
            parsed_path = urllib.parse.urlparse(clean_url).path
            _, ext = os.path.splitext(parsed_path)
            if not ext or len(ext) > 5:
                ext = ".jpg"
            dest_filename = f"image_{img_idx:02d}{ext.lower()}"
            dest_path = os.path.join(img_dir, dest_filename)
            download_tasks.append((clean_url, dest_path, handle))

    print(f"[+] Queued {len(download_tasks)} total images across {len(products)} products.")

    # 5. Download images concurrently
    print(f"\n[*] Downloading media assets (Concurrency: {MAX_WORKERS})...")
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(download_single_image, url, path): (url, path, handle)
            for url, path, handle in download_tasks
        }
        for future in as_completed(future_map):
            url, path, handle = future_map[future]
            try:
                if future.result():
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                fail_count += 1
                print(f"    [!] Error downloading {url}: {e}", file=sys.stderr)

            completed = success_count + fail_count
            if completed % 25 == 0 or completed == len(download_tasks):
                print(f"    Progress: {completed}/{len(download_tasks)} images ({success_count} succeeded, {fail_count} failed)")

    print(f"\n[+] Image download complete: {success_count} successful, {fail_count} failed.")
    return True


if __name__ == "__main__":
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    success = export_catalog(workspace)
    if not success:
        sys.exit(1)
