# The Healthy Pepper Product Archive & Shopify Import Package

This directory contains the complete product catalog, descriptions, metadata, and high-resolution media downloaded from [thehealthypepper.com](https://thehealthypepper.com), formatted for instant 1-click import into another Shopify store.

---

## Catalog Overview

- **Total Products:** 90
- **Total Product Variants & Image Rows:** 508
- **Total Downloaded Images:** 508 high-resolution assets (880.54 MB)
- **Status:** 100% complete with 0 failures

---

## Directory Structure

```
d:\thehealthypepper\
├── data\
│   ├── shopify_products_import.csv    # Official Shopify CSV (1-click import into any Shopify store)
│   ├── products.json                  # Complete raw JSON payload of all 90 products
│   └── products_summary.json          # Index of all products (Title, Handle, Price, SKU, Tags)
├── products\
│   ├── [product-handle-1]\
│   │   ├── metadata.json              # Full individual product metadata JSON
│   │   ├── description.html           # HTML formatted body description
│   │   └── images\                    # High-resolution original images
│   │       ├── image_01.jpg
│   │       └── ...
│   └── ... (all 90 product folders)
├── scripts\
│   ├── export_products.py             # Reusable extraction & media downloader pipeline
│   ├── shopify_formatter.py           # Shopify CSV converter & handle sanitizer
│   └── verify_export.py               # Complete catalog integrity & audit runner
├── docs\
│   └── superpowers\
│       ├── specs\                     # Approved architecture design specification
│       └── plans\                     # Implementation plan
└── tests\
    └── test_shopify_formatter.py      # Unit tests
```

---

## How to Import Into Your New Shopify Store

1. Log into your **Shopify Admin** on your destination store.
2. In the left navigation, go to **Products**.
3. Click the **Import** button (top right).
4. Click **Add file** and select:
   ```
   d:\thehealthypepper\data\shopify_products_import.csv
   ```
5. *(Optional)* Check *"Overwrite any current products that have the same handle"* if updating existing items.
6. Click **Upload and continue**.
7. Shopify will preview the product columns, titles, and images. Click **Import products**.
8. Shopify will automatically download and link all 508 high-resolution product images directly into your new store!

---

## Verifying Catalog Integrity

To verify the files and media integrity at any time, run:

```bash
python scripts/verify_export.py
```
