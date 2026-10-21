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
    """Sanitize product handle for cross-platform safe directory names."""
    if not handle:
        return "unnamed-product"
    clean = re.sub(r'[\\/*?:"<>|]', '_', str(handle))
    return clean.strip().strip('.')

def extract_product_summary(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract a lightweight index of all products."""
    summary = []
    for p in products:
        variants = p.get("variants", []) or []
        images = p.get("images", []) or []
        prices = []
        for v in variants:
            try:
                if v.get("price") is not None:
                    prices.append(float(v["price"]))
            except (ValueError, TypeError):
                pass
        
        summary.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "handle": p.get("handle"),
            "vendor": p.get("vendor"),
            "product_type": p.get("product_type"),
            "variants_count": len(variants),
            "images_count": len(images),
            "min_price": min(prices) if prices else 0.0,
            "max_price": max(prices) if prices else 0.0,
            "tags": p.get("tags")
        })
    return summary

def format_shopify_csv(products: List[Dict[str, Any]], output_csv_path: str) -> int:
    """
    Format products into the standard Shopify multi-row product CSV.
    Returns the total number of data rows written.
    """
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
            
            options = p.get("options", []) or []
            opt1_name = options[0]["name"] if len(options) > 0 else "Title"
            opt2_name = options[1]["name"] if len(options) > 1 else ""
            opt3_name = options[2]["name"] if len(options) > 2 else ""
            
            variants = p.get("variants", []) or []
            images = p.get("images", []) or []
            
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
                    row["Option1 Value"] = str(v.get("option1") or "Default Title")
                    row["Option2 Value"] = str(v.get("option2") or "")
                    row["Option3 Value"] = str(v.get("option3") or "")
                    row["Variant SKU"] = str(v.get("sku") or "")
                    row["Variant Grams"] = str(v.get("grams", 0) or 0)
                    row["Variant Inventory Tracker"] = "shopify"
                    row["Variant Inventory Qty"] = "100"
                    row["Variant Inventory Policy"] = "deny"
                    row["Variant Fulfillment Service"] = "manual"
                    row["Variant Price"] = str(v.get("price") or "")
                    row["Variant Compare At Price"] = str(v.get("compare_at_price") or "")
                    row["Variant Requires Shipping"] = "TRUE" if v.get("requires_shipping", True) else "FALSE"
                    row["Variant Taxable"] = "TRUE" if v.get("taxable", True) else "FALSE"
                    row["Variant Barcode"] = str(v.get("barcode") or "")
                
                if img:
                    src = img.get("src", "")
                    clean_src = src.split("?")[0] if src else ""
                    row["Image Src"] = clean_src
                    row["Image Position"] = str(img.get("position", i + 1))
                    row["Image Alt Text"] = str(img.get("alt") or "")
                
                writer.writerow(row)
                total_rows += 1
                
    return total_rows
