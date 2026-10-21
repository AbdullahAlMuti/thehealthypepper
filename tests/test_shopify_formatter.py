import unittest
import csv
import os
import tempfile
from scripts.shopify_formatter import sanitize_handle, format_shopify_csv, extract_product_summary

class TestShopifyFormatter(unittest.TestCase):
    def test_sanitize_handle(self):
        self.assertEqual(sanitize_handle("clean-handle"), "clean-handle")
        self.assertEqual(sanitize_handle("bad:handle/test*?"), "bad_handle_test__")
        self.assertEqual(sanitize_handle(""), "unnamed-product")

    def test_extract_product_summary(self):
        products = [{
            "id": 1,
            "title": "Sample",
            "handle": "sample",
            "variants": [{"price": "10.00"}, {"price": "15.00"}],
            "images": [{"src": "img.jpg"}]
        }]
        summary = extract_product_summary(products)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["title"], "Sample")
        self.assertEqual(summary[0]["variants_count"], 2)
        self.assertEqual(summary[0]["images_count"], 1)
        self.assertEqual(summary[0]["min_price"], 10.0)

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
                self.assertEqual(rows[1]["Handle"], "test-product")
                self.assertEqual(rows[1]["Variant Price"], "29.99")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
