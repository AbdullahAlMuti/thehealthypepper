import unittest
import os
import tempfile
from scripts.export_products import sanitize_title_folder

class TestProductsDirectory(unittest.TestCase):
    def test_sanitize_title_folder(self):
        self.assertEqual(sanitize_title_folder("Pepper Bliss"), "Pepper Bliss")
        self.assertEqual(sanitize_title_folder("Lion's Mane Mushroom"), "Lion's Mane Mushroom")
        self.assertEqual(sanitize_title_folder("Pure3 100% Whey Protein Isolate (Vanilla)"), "Pure3 100% Whey Protein Isolate (Vanilla)")
        self.assertEqual(sanitize_title_folder("Product: Special? <Tag>"), "Product- Special- -Tag-")

    def test_products_structure(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        products_dir = os.path.join(root, "Products")
        self.assertTrue(os.path.exists(products_dir), "Products directory must exist")
        
        sample_folder = os.path.join(products_dir, "Pepper Bliss")
        self.assertTrue(os.path.exists(sample_folder), "Pepper Bliss folder must exist")
        self.assertTrue(os.path.exists(os.path.join(sample_folder, "images")), "images folder must exist in Pepper Bliss")
        self.assertTrue(os.path.exists(os.path.join(sample_folder, "-images")), "-images junction must exist in Pepper Bliss")
        
        # Verify images exist in Pepper Bliss
        images = os.listdir(os.path.join(sample_folder, "images"))
        self.assertGreater(len(images), 0, "Pepper Bliss must have images")

if __name__ == "__main__":
    unittest.main()
