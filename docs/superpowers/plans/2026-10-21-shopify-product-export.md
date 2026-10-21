# Shopify Product Export & Media Archive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fetch all 90 products from `thehealthypepper.com`, generate a 1-click Shopify import CSV (`data/shopify_products_import.csv`), save master raw JSONs (`data/products.json`, `data/products_summary.json`), create per-product folders under `products/[handle]/` with metadata, HTML description, and download all original high-resolution media images.

**Architecture:** Python-based modular CLI extractor with separate modules/functions for API fetching, Shopify CSV conversion, filesystem organization, and multi-threaded image downloading with retry/validation.

**Tech Stack:** Python 3.13, `requests`, `csv`, `json`, `concurrent.futures`, `unittest`.

## Global Constraints

- Source URL: `https://thehealthypepper.com/products.json`
- Target root: `d:\thehealthypepper`
- All product handles sanitized for Windows path safety (`\/:*?"<>|`)
- Shopify CSV columns must strictly adhere to official Shopify Product CSV specification
- No 0-byte corrupt files permitted; retry on failed downloads
- Python standard library + `requests` only

---

### Task 1: Core Extractor & Shopify CSV Formatter

**Files:**
- Create: `scripts/shopify_formatter.py`
- Create: `tests/test_shopify_formatter.py`

**Interfaces:**
- Produces: `sanitize_handle(title_or_handle: str) -> str`
- Produces: `format_shopify_csv(products: list[dict], output_csv_path: str) -> int`
- Produces: `extract_product_summary(products: list[dict]) -> list[dict]`

- [ ] **Step 1: Write unit tests for CSV formatter and handle sanitizer**

Create `tests/test_shopify_formatter.py`:
```python
import unittest
import csv
import os
import tempfile
from scripts.shopify_formatter import sanitize_handle, format_shopify_csv, extract_product_summary

class TestShopifyFormatter(unittest.TestCase):
    def test_sanitize_handle(self):
        self.assertEqual(sanitize_handle("clean-handle"), "clean-handle")
        self.assertEqual(sanitize_handle("bad:handle/test*?"), "bad_handle_test__")

    def test_format_shopify_csv(self):
        sample_products = [{
            "id": 12345,
            "title": "Test Product",
            "handle": "test-product",
            "body_html": "<p>Description</p>",
            "vendor": "Healthy Pepper",
            "product_type": "Supplements",
            "tags": ["Health", "Vitamins"],
            "options": [{"name": "Size", "values": ["Small", "Large"]}],
            "variants": [
                {
                    "id": 1,
                    "title": "Small",
                    "price": "19.99",
                    "compare_at_price": "24.99",
                    "sku": "TP-S",
                    "grams": 200,
                    "barcode": "12345678",
                    "option1": "Small"
                },
                {
                    "id": 2,
                    "title": "Large",
                    "price": "29.99",
                    "compare_at_price": None,
                    "sku": "TP-L",
                    "grams": 400,
                    "barcode": "12345679",
                    "option1": "Large"
                }
            ],
            "images": [
                {"src": "https://cdn.shopify.com/s/files/img1.jpg?v=1", "position": 1, "alt": "Front view"},
                {"src": "https://cdn.shopify.com/s/files/img2.jpg?v=1", "position": 2, "alt": "Back view"}
            ]
        }]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w") as f:
            temp_path = f.name
        try:
            row_count = format_shopify_csv(sample_products, temp_path)
            self.assertGreater(row_count, 1)
            with open(temp_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertIn("Handle", reader.fieldnames)
                self.assertIn("Title", reader.fieldnames)
                self.assertIn("Variant Price", reader.fieldnames)
                self.assertEqual(rows[0]["Title"], "Test Product")
                self.assertEqual(rows[0]["Variant Price"], "19.99")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_shopify_formatter.py`
Expected: FAIL (ModuleNotFoundError: No module named 'scripts.shopify_formatter')

- [ ] **Step 3: Implement `scripts/shopify_formatter.py`**

```python
import csv
import re
from typing import List, Dict, Any

SHOPIFY_CSV_HEADERS = [
    "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type", "Tags",
    "Published", "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value",
    "Option3 Name", "Option3 Value", "Variant SKU", "Variant Grams",
    "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy",
    "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price",
    "Variant Requires Shipping", "Variant Taxable", "Variant Barcode",
    "Image Src", "Image Position", "Image Alt Text", "Gift Card",
    "SEO Title", "SEO Description", "Status"
]

def sanitize_handle(handle: str) -> str:
    if not handle:
        return "unnamed-product"
    clean = re.sub(r'[\\/*?:"<>|]', '_', handle)
    return clean.strip().strip('.')

def extract_product_summary(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary = []
    for p in products:
        summary.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "handle": p.get("handle"),
            "vendor": p.get("vendor"),
            "product_type": p.get("product_type"),
            "variants_count": len(p.get("variants", [])),
            "images_count": len(p.get("images", [])),
            "min_price": min([float(v.get("price", 0)) for v in p.get("variants", [])]) if p.get("variants") else 0,
            "tags": p.get("tags")
        })
    return summary

def format_shopify_csv(products: List[Dict[str, Any]], output_csv_path: str) -> int:
    total_rows = 0
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SHOPIFY_CSV_HEADERS)
        writer.writeheader()
        
        for p in products:
            handle = p.get("handle", "")
            title = p.get("title", "")
            body_html = p.get("body_html", "") or ""
            vendor = p.get("vendor", "")
            product_type = p.get("product_type", "")
            tags = p.get("tags", "")
            if isinstance(tags, list):
                tags = ", ".join(tags)
            
            options = p.get("options", [])
            opt1_name = options[0]["name"] if len(options) > 0 else ""
            opt2_name = options[1]["name"] if len(options) > 1 else ""
            opt3_name = options[2]["name"] if len(options) > 2 else ""
            
            variants = p.get("variants", [])
            images = p.get("images", [])
            
            max_rows = max(len(variants), len(images), 1)
            for i in range(max_rows):
                v = variants[i] if i < len(variants) else None
                img = images[i] if i < len(images) else None
                
                row = {h: "" for h in SHOPIFY_CSV_HEADERS}
                row["Handle"] = handle
                
                if i == 0:
                    row["Title"] = title
                    row["Body (HTML)"] = body_html
                    row["Vendor"] = vendor
                    row["Type"] = product_type
                    row["Tags"] = tags
                    row["Published"] = "TRUE"
                    row["Status"] = "active"
                    row["Option1 Name"] = opt1_name
                    row["Option2 Name"] = opt2_name
                    row["Option3 Name"] = opt3_name
                
                if v:
                    row["Option1 Value"] = v.get("option1", "") or ""
                    row["Option2 Value"] = v.get("option2", "") or ""
                    row["Option3 Value"] = v.get("option3", "") or ""
                    row["Variant SKU"] = v.get("sku", "") or ""
                    row["Variant Grams"] = str(v.get("grams", 0) or 0)
                    row["Variant Inventory Tracker"] = "shopify"
                    row["Variant Inventory Qty"] = "100"
                    row["Variant Inventory Policy"] = "deny"
                    row["Variant Fulfillment Service"] = "manual"
                    row["Variant Price"] = str(v.get("price", "") or "")
                    row["Variant Compare At Price"] = str(v.get("compare_at_price", "") or "")
                    row["Variant Requires Shipping"] = "TRUE" if v.get("requires_shipping", True) else "FALSE"
                    row["Variant Taxable"] = "TRUE" if v.get("taxable", True) else "FALSE"
                    row["Variant Barcode"] = str(v.get("barcode", "") or "")
                
                if img:
                    src = img.get("src", "")
                    clean_src = src.split("?")[0] if src else ""
                    row["Image Src"] = clean_src
                    row["Image Position"] = str(img.get("position", i + 1))
                    row["Image Alt Text"] = img.get("alt", "") or ""
                
                writer.writerow(row)
                total_rows += 1
                
    return total_rows
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_shopify_formatter.py`
Expected: PASS

- [ ] **Step 5: Commit changes**

Run:
```bash
git add scripts/shopify_formatter.py tests/test_shopify_formatter.py
git commit -m "feat: implement shopify csv formatter and handle sanitizer"
```

---

### Task 2: Downloader Engine & File Organizer

**Files:**
- Create: `scripts/export_products.py`
- Test: `python scripts/export_products.py --dry-run`

**Interfaces:**
- Consumes: `shopify_formatter.py`
- Produces: `data/products.json`, `data/products_summary.json`, `data/shopify_products_import.csv`
- Produces: `products/[handle]/metadata.json`, `products/[handle]/description.html`, `products/[handle]/images/*`

- [ ] **Step 1: Implement full export script in `scripts/export_products.py`**
  - Fetches all products using pagination from `https://thehealthypepper.com/products.json?limit=250&page=1`
  - Saves raw data to `data/products.json`
  - Saves summary to `data/products_summary.json`
  - Generates `data/shopify_products_import.csv`
  - Sets up directories for each product in `products/[sanitized_handle]/`
  - Saves `metadata.json` and `description.html` in each product folder
  - Concurrently downloads all media files into `products/[handle]/images/` with retry logic and non-zero size checks
  - Outputs a complete summary log

- [ ] **Step 2: Run execution of export script**

Run: `python scripts/export_products.py`
Expected: Successfully fetches 90 products, generates CSV, creates 90 folders, downloads all media assets.

- [ ] **Step 3: Commit code**

Run:
```bash
git add scripts/export_products.py
git commit -m "feat: complete product extraction and media downloader engine"
```

---

### Task 3: Comprehensive Verification & Audit

**Files:**
- Create: `scripts/verify_export.py`

- [ ] **Step 1: Write and run verification script**
  - Verify `data/products.json` contains 90 items.
  - Verify `data/shopify_products_import.csv` exists and has valid rows with required Shopify headers.
  - Verify `products/` contains 90 directories.
  - Verify each directory has `metadata.json`, `description.html`, and `images/`.
  - Verify no image is 0 bytes.
  - Count total images downloaded and print full catalog audit.

- [ ] **Step 2: Commit verification script and updated task checklist**

Run:
```bash
git add scripts/verify_export.py
git commit -m "test: add verification audit script"
```
