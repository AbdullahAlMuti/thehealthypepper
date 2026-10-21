# Design Specification: The Healthy Pepper Product Archive & Shopify Import Export

**Date:** 2026-10-21  
**Target Source:** `https://thehealthypepper.com` (Shopify Storefront)  
**Destination:** `d:\thehealthypepper`

---

## 1. Objective & Scope

Extract, organize, and archive all 90 products from `thehealthypepper.com` into:
1. **Raw JSON & Metadata Archive:** A structured directory per product containing individual metadata JSON, rendered HTML descriptions, and full-resolution media images.
2. **Master Dataset:** A root `data/products.json` with the complete API response and a `data/products_summary.json` with high-level catalog statistics.
3. **Shopify 1-Click Import CSV:** An official Shopify product import CSV file (`data/shopify_products_import.csv`) referencing all handles, titles, body descriptions, vendors, product types, tags, variants, prices, SKUs, and CDN image URLs so the user can import the catalog seamlessly into a new Shopify store.

---

## 2. Directory Layout

The workspace root will be structured as follows:

```
d:\thehealthypepper\
├── data\
│   ├── products.json                  # Complete raw 90 products JSON from Shopify API
│   ├── products_summary.json          # Index of all products (id, title, handle, variants count, images count)
│   └── shopify_products_import.csv    # Official Shopify-compatible CSV ready for store import
├── products\
│   ├── [product-handle]\
│   │   ├── metadata.json              # Specific product details, variants, tags, options
│   │   ├── description.html           # Full HTML product description
│   │   └── images\
│   │       ├── image_01.jpg           # High-resolution original image
│   │       ├── image_02.jpg
│   │       └── ...
│   └── ... (90 folders total)
├── scripts\
│   └── export_products.py             # Python extraction, conversion, and download engine
└── docs\
    └── superpowers\
        └── specs\
            └── 2026-10-21-shopify-product-export-design.md
```

---

## 3. Data Processing & Mapping Architecture

### 3.1 Fetching Strategy
- Retrieve product catalog from `https://thehealthypepper.com/products.json?limit=250&page=1`.
- Verify total product count (90 products).
- Check for subsequent pages to guarantee complete coverage.

### 3.2 Individual Product Organization
For each product:
- **Folder naming:** Sanitized product `handle` (e.g., `glp-1-daily-nutrition-pack`). If handle contains special Windows filesystem characters (`\ / : * ? " < > |`), clean them.
- **`metadata.json`:** Contains the product's full payload (ID, title, handle, vendor, product_type, tags, options, variants, image metadata).
- **`description.html`:** Clean UTF-8 encoded `body_html` string for easy inspection or import.
- **Images:** Strip URL query parameters (`?v=...`, `_medium`, etc.) to obtain the highest-resolution source image from Shopify CDN (`https://cdn.shopify.com/s/files/...`). Save sequentially into `products/[handle]/images/image_01.ext`, `image_02.ext`.

### 3.3 Shopify Product CSV Mapping
To enable immediate 1-click import into another Shopify store, the script will map products to Shopify's standard CSV columns:
- `Handle`
- `Title`
- `Body (HTML)`
- `Vendor`
- `Product Category`
- `Type`
- `Tags`
- `Published` (TRUE)
- `Option1 Name`, `Option1 Value`
- `Option2 Name`, `Option2 Value`
- `Option3 Name`, `Option3 Value`
- `Variant SKU`
- `Variant Grams`
- `Variant Inventory Tracker` (shopify)
- `Variant Inventory Qty` (100 default)
- `Variant Inventory Policy` (deny)
- `Variant Fulfillment Service` (manual)
- `Variant Price`
- `Variant Compare At Price`
- `Variant Requires Shipping` (TRUE)
- `Variant Taxable` (TRUE)
- `Variant Barcode`
- `Image Src` (Original live Shopify CDN URL)
- `Image Position`
- `Image Alt Text`
- `Gift Card` (FALSE)
- `SEO Title`, `SEO Description`
- `Status` (active)

When a product has multiple variants and/or multiple images, the CSV will follow Shopify's multi-row standard:
- First row contains Title, Body, Vendor, Type, Tags, Option definitions, first Variant details, and first Image.
- Subsequent rows repeat the `Handle` and provide additional Variants and/or additional `Image Src` and `Image Position`.

---

## 4. Concurrency, Network Resilience & Idempotency

1. **Async / Worker Thread Pool:**
   - Use `concurrent.futures.ThreadPoolExecutor` (concurrency 8-10) for image downloading to maximize throughput without triggering rate limits.
2. **Exponential Backoff & Retries:**
   - Implement retry logic (up to 3 attempts with jittered exponential backoff) for any transient HTTP 429 or 5xx errors.
3. **Idempotency & Checkpointing:**
   - If a file exists and has size > 0 bytes, skip downloading to allow resume capability if process is halted.
4. **Validation:**
   - Verify every downloaded image has non-zero size.

---

## 5. Verification & Testing Criteria

The implementation is verified complete when:
1. `data/products.json` exists and parses cleanly into 90 product objects.
2. `data/shopify_products_import.csv` exists, contains non-empty rows for all 90 products and variants, and adheres to Shopify's CSV structure.
3. 90 subdirectories exist inside `products/`, each containing `metadata.json`, `description.html`, and non-empty `images/` directory.
4. Total image count matches the total number of images declared across all 90 products in the source JSON.
5. All image files are non-zero byte files.
