"""Test if foreign keys are enabled in test database"""
import unittest
from tests.base_test import BaseTestCase
from models import db, MergeSession, Package, ObjectLookup, PackageObjectMapping


class TestForeignKeys(BaseTestCase):
    """Test foreign key constraints"""

    def test_foreign_keys_enabled(self):
        """Test that foreign keys are enabled"""
        result = db.session.execute(db.text("PRAGMA foreign_keys")).fetchone()
        print(f"Foreign keys enabled: {result}")
        self.assertEqual(result[0], 1, "Foreign keys should be enabled")

    def test_foreign_key_constraint_works(self):
        """Test that foreign key constraints are enforced"""
        # Try to insert a package_object_mapping with non-existent package_id
        # This should fail with IntegrityError
        
        # First create a valid object
        obj = ObjectLookup(
            uuid='test-uuid',
            name='Test Object',
            object_type='Interface'
        )
        db.session.add(obj)
        db.session.flush()
        
        # Try to create mapping with non-existent package_id
        mapping = PackageObjectMapping(
            package_id=999,  # Doesn't exist
            object_id=obj.id
        )
        db.session.add(mapping)
        
        # This should raise IntegrityError
        with self.assertRaises(Exception) as context:
            db.session.flush()
        
        print(f"Exception: {context.exception}")
        self.assertIn("FOREIGN KEY", str(context.exception))


if __name__ == '__main__':
    unittest.main()
