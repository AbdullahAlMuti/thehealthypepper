"""
Verification and Audit Script for The Healthy Pepper Product Archive
Checks that all products, metadata, descriptions, images, and CSV files are complete and valid.
"""

import os
import sys
import json
import csv

def run_verification(workspace_root: str):
    data_dir = os.path.join(workspace_root, "data")
    products_dir = os.path.join(workspace_root, "Products")
    
    errors = []
    
    # 1. Verify data/products.json
    raw_json_path = os.path.join(data_dir, "products.json")
    if not os.path.exists(raw_json_path):
        errors.append(f"Missing {raw_json_path}")
        return False, errors
    
    with open(raw_json_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    products = catalog.get("products", [])
    total_products = len(products)
    print(f"[VERIFY] Found {total_products} products in data/products.json")
    if total_products == 0:
        errors.append("data/products.json contains 0 products")
    
    # 2. Verify products_summary.json
    summary_path = os.path.join(data_dir, "products_summary.json")
    if not os.path.exists(summary_path):
        errors.append(f"Missing {summary_path}")
    else:
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        if len(summary) != total_products:
            errors.append(f"Summary count ({len(summary)}) != products count ({total_products})")
        print(f"[VERIFY] products_summary.json verified with {len(summary)} entries")

    # 3. Verify shopify_products_import.csv
    csv_path = os.path.join(data_dir, "shopify_products_import.csv")
    if not os.path.exists(csv_path):
        errors.append(f"Missing {csv_path}")
    else:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"[VERIFY] shopify_products_import.csv verified with {len(rows)} data rows")
        if len(rows) < total_products:
            errors.append(f"CSV row count ({len(rows)}) is less than total products ({total_products})")
            
    # 4. Verify product folders, metadata, html descriptions, images, and -images junctions
    product_folders = [d for d in os.listdir(products_dir) if os.path.isdir(os.path.join(products_dir, d))]
    print(f"[VERIFY] Found {len(product_folders)} folders in Products/")
    if len(product_folders) != total_products:
        errors.append(f"Product folders count ({len(product_folders)}) != total products ({total_products})")
        
    total_images_found = 0
    total_images_size_bytes = 0
    zero_byte_images = []
    junction_count = 0
    
    for folder_name in product_folders:
        folder_path = os.path.join(products_dir, folder_name)
        meta_file = os.path.join(folder_path, "metadata.json")
        desc_file = os.path.join(folder_path, "description.html")
        images_dir = os.path.join(folder_path, "images")
        dash_images_dir = os.path.join(folder_path, "-images")
        
        if not os.path.exists(meta_file):
            errors.append(f"Missing metadata.json in {folder_name}")
        if not os.path.exists(desc_file):
            errors.append(f"Missing description.html in {folder_name}")
        if not os.path.exists(images_dir):
            errors.append(f"Missing images directory in {folder_name}")
        else:
            images = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
            total_images_found += len(images)
            for img in images:
                img_path = os.path.join(images_dir, img)
                sz = os.path.getsize(img_path)
                if sz == 0:
                    zero_byte_images.append(img_path)
                total_images_size_bytes += sz

        if os.path.exists(dash_images_dir):
            junction_count += 1
        else:
            errors.append(f"Missing -images junction in {folder_name}")
                
    if zero_byte_images:
        errors.append(f"Found {len(zero_byte_images)} 0-byte images")
        
    print(f"[VERIFY] Total downloaded images: {total_images_found}")
    print(f"[VERIFY] Total active -images junctions: {junction_count}/{len(product_folders)}")
    print(f"[VERIFY] Total media size: {total_images_size_bytes / (1024 * 1024):.2f} MB")
    
    if errors:
        print("\n[!] VERIFICATION FAILURES:")
        for err in errors:
            print(f"    - {err}")
        return False
    else:
        print("\n[+] ALL AUDIT CHECKS PASSED SUCCESSFULLY!")
        return True

if __name__ == "__main__":
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    success = run_verification(workspace)
    if not success:
        sys.exit(1)
