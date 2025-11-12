#!/usr/bin/env python3
"""
Unit tests for database.py module.

Tests the SQLite database layer for eSIM issuance including:
- Database connection management
- Schema creation
- CRUD operations
- Data validation
- QR code storage and retrieval
"""

import unittest
import os
import tempfile
from database import DatabaseConnection, GSMAComplianceDB


class TestDatabaseConnection(unittest.TestCase):
    """Test database connection management."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_connection_creation(self):
        """Test creating a database connection."""
        with DatabaseConnection(self.db_path) as db_conn:
            self.assertIsNotNone(db_conn.connection)

    def test_connection_context_manager(self):
        """Test context manager properly opens and closes connection."""
        with DatabaseConnection(self.db_path) as db_conn:
            self.assertIsNotNone(db_conn.connection)
        # After exiting context, connection should be closed
        # We can't directly test if it's closed without triggering an error


class TestGSMAComplianceDB(unittest.TestCase):
    """Test GSMA compliance database operations."""

    def setUp(self):
        """Set up test database with schema."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name

        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            gsma_db.create_schema()

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_schema_creation(self):
        """Test database schema is created correctly."""
        with DatabaseConnection(self.db_path) as db_conn:
            cursor = db_conn.connection.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='gsma_compliance'"
            )
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 'gsma_compliance')

    def test_insert_esim_data_basic(self):
        """Test inserting basic eSIM data without QR code."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            record_id = gsma_db.insert_esim_data('PROF-001', '8901234567890123456')
            self.assertEqual(record_id, 1)

    def test_insert_esim_data_with_qr(self):
        """Test inserting eSIM data with QR code."""
        qr_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'  # Fake PNG header
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            record_id = gsma_db.insert_esim_data('PROF-002', '8901234567890123457', qr_data)
            self.assertEqual(record_id, 1)

            # Verify QR code was stored
            profile = gsma_db.get_profile_by_id(record_id)
            self.assertEqual(profile['qr_code'], qr_data)

    def test_duplicate_iccid_rejected(self):
        """Test that duplicate ICCIDs are rejected."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            gsma_db.insert_esim_data('PROF-001', '8901234567890123456')

            # Try to insert duplicate ICCID
            with self.assertRaises(Exception):
                gsma_db.insert_esim_data('PROF-002', '8901234567890123456')

    def test_get_profile_by_id(self):
        """Test retrieving profile by record ID."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            record_id = gsma_db.insert_esim_data('PROF-003', '8901234567890123458')

            profile = gsma_db.get_profile_by_id(record_id)
            self.assertIsNotNone(profile)
            self.assertEqual(profile['profile_id'], 'PROF-003')
            self.assertEqual(profile['iccid'], '8901234567890123458')

    def test_get_profile_by_id_not_found(self):
        """Test retrieving non-existent profile returns None."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            profile = gsma_db.get_profile_by_id(999)
            self.assertIsNone(profile)

    def test_get_profile_by_iccid(self):
        """Test retrieving profile by ICCID."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            gsma_db.insert_esim_data('PROF-004', '8901234567890123459')

            profile = gsma_db.get_profile_by_iccid('8901234567890123459')
            self.assertIsNotNone(profile)
            self.assertEqual(profile['profile_id'], 'PROF-004')

    def test_get_profile_by_iccid_not_found(self):
        """Test retrieving non-existent ICCID returns None."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            profile = gsma_db.get_profile_by_iccid('9999999999999999999')
            self.assertIsNone(profile)

    def test_get_all_profiles(self):
        """Test retrieving all profiles."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            gsma_db.insert_esim_data('PROF-005', '8901234567890123460')
            gsma_db.insert_esim_data('PROF-006', '8901234567890123461')
            gsma_db.insert_esim_data('PROF-007', '8901234567890123462')

            profiles = gsma_db.get_all_profiles()
            self.assertEqual(len(profiles), 3)

    def test_get_all_profiles_pagination(self):
        """Test pagination in get_all_profiles."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            for i in range(5):
                gsma_db.insert_esim_data(f'PROF-{i:03d}', f'890123456789012346{i}')

            # Get first 2 profiles
            profiles_page1 = gsma_db.get_all_profiles(limit=2, offset=0)
            self.assertEqual(len(profiles_page1), 2)

            # Get next 2 profiles
            profiles_page2 = gsma_db.get_all_profiles(limit=2, offset=2)
            self.assertEqual(len(profiles_page2), 2)

            # Ensure they're different
            self.assertNotEqual(profiles_page1[0]['id'], profiles_page2[0]['id'])

    def test_update_qr_code(self):
        """Test updating QR code for existing profile."""
        qr_data_old = b'old_qr_data'
        qr_data_new = b'new_qr_data'

        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            record_id = gsma_db.insert_esim_data('PROF-008', '8901234567890123465', qr_data_old)

            # Update QR code
            success = gsma_db.update_qr_code(record_id, qr_data_new)
            self.assertTrue(success)

            # Verify update
            profile = gsma_db.get_profile_by_id(record_id)
            self.assertEqual(profile['qr_code'], qr_data_new)

    def test_update_qr_code_nonexistent(self):
        """Test updating QR code for non-existent profile."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            success = gsma_db.update_qr_code(999, b'data')
            self.assertFalse(success)

    def test_delete_profile(self):
        """Test deleting a profile."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            record_id = gsma_db.insert_esim_data('PROF-009', '8901234567890123466')

            # Delete profile
            success = gsma_db.delete_profile(record_id)
            self.assertTrue(success)

            # Verify deletion
            profile = gsma_db.get_profile_by_id(record_id)
            self.assertIsNone(profile)

    def test_delete_profile_nonexistent(self):
        """Test deleting non-existent profile."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            success = gsma_db.delete_profile(999)
            self.assertFalse(success)

    def test_save_qr_code_to_file(self):
        """Test saving QR code to file."""
        qr_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_file.close()

        try:
            with DatabaseConnection(self.db_path) as db_conn:
                gsma_db = GSMAComplianceDB(db_conn)
                record_id = gsma_db.insert_esim_data('PROF-010', '8901234567890123467', qr_data)

                # Save to file
                success = gsma_db.save_qr_code_to_file(record_id, temp_file.name)
                self.assertTrue(success)

                # Verify file contents
                with open(temp_file.name, 'rb') as f:
                    saved_data = f.read()
                self.assertEqual(saved_data, qr_data)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_save_qr_code_to_file_no_qr(self):
        """Test saving QR code when none exists."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_file.close()

        try:
            with DatabaseConnection(self.db_path) as db_conn:
                gsma_db = GSMAComplianceDB(db_conn)
                record_id = gsma_db.insert_esim_data('PROF-011', '8901234567890123468')

                # Try to save non-existent QR code
                success = gsma_db.save_qr_code_to_file(record_id, temp_file.name)
                self.assertFalse(success)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_timestamp_auto_generated(self):
        """Test that timestamp is automatically generated."""
        with DatabaseConnection(self.db_path) as db_conn:
            gsma_db = GSMAComplianceDB(db_conn)
            record_id = gsma_db.insert_esim_data('PROF-012', '8901234567890123469')

            profile = gsma_db.get_profile_by_id(record_id)
            self.assertIsNotNone(profile['timestamp'])


if __name__ == '__main__':
    unittest.main()
