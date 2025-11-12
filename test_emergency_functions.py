"""
Test suite for emergency functions module.

Tests cover:
1. Emergency configuration creation and validation
2. Database operations (SQLite)
3. RSM server integration and fallback mechanisms
4. Regional configuration management
5. Emergency number validation
6. Configuration import/export
"""

import unittest
import os
import json
import tempfile
from emergency_functions import (
    EmergencyFunctionManager,
    EmergencyConfig,
    DatabaseManager,
    RSMServerManager,
    DatabaseType,
    RegionCode
)


class TestEmergencyConfig(unittest.TestCase):
    """Test emergency configuration data structure"""

    def test_config_creation(self):
        """Test creating a basic emergency configuration"""
        config = EmergencyConfig()
        self.assertEqual(config.region, RegionCode.US.value)
        self.assertEqual(config.emergency_numbers, ["911"])
        self.assertEqual(config.network_priority, 1)

    def test_config_to_dict(self):
        """Test converting configuration to dictionary"""
        config = EmergencyConfig()
        config.region = RegionCode.EU.value
        config.emergency_numbers = ["112"]

        config_dict = config.to_dict()
        self.assertEqual(config_dict["region"], RegionCode.EU.value)
        self.assertEqual(config_dict["emergency_numbers"], ["112"])

    def test_config_from_dict(self):
        """Test creating configuration from dictionary"""
        data = {
            "region": RegionCode.UK.value,
            "emergency_numbers": ["999", "112"],
            "psap_routing_code": "UK-PSAP-001",
            "network_priority": 1
        }

        config = EmergencyConfig.from_dict(data)
        self.assertEqual(config.region, RegionCode.UK.value)
        self.assertEqual(len(config.emergency_numbers), 2)
        self.assertIn("999", config.emergency_numbers)
        self.assertIn("112", config.emergency_numbers)


class TestDatabaseManager(unittest.TestCase):
    """Test database operations"""

    def setUp(self):
        """Create temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(
            DatabaseType.SQLITE,
            self.temp_db.name
        )

    def tearDown(self):
        """Clean up temporary database"""
        self.db_manager.close()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_database_connection(self):
        """Test database connection"""
        result = self.db_manager.connect()
        self.assertTrue(result)
        self.assertIsNotNone(self.db_manager.connection)

    def test_schema_initialization(self):
        """Test database schema creation"""
        self.db_manager.connect()
        result = self.db_manager.initialize_schema()
        self.assertTrue(result)

    def test_save_and_load_config(self):
        """Test saving and loading emergency configuration"""
        self.db_manager.connect()
        self.db_manager.initialize_schema()

        # Create and save config
        config = EmergencyConfig()
        config.region = RegionCode.US.value
        config.emergency_numbers = ["911"]
        config.psap_routing_code = "US-TEST-001"

        result = self.db_manager.save_emergency_config("test_profile", config)
        self.assertTrue(result)

        # Load config
        loaded_config = self.db_manager.load_emergency_config("test_profile")
        self.assertIsNotNone(loaded_config)
        self.assertEqual(loaded_config.region, RegionCode.US.value)
        self.assertEqual(loaded_config.emergency_numbers, ["911"])

    def test_load_nonexistent_config(self):
        """Test loading a configuration that doesn't exist"""
        self.db_manager.connect()
        self.db_manager.initialize_schema()

        loaded_config = self.db_manager.load_emergency_config("nonexistent")
        self.assertIsNone(loaded_config)


class TestRSMServerManager(unittest.TestCase):
    """Test RSM server management"""

    def test_rsm_manager_initialization(self):
        """Test RSM server manager initialization"""
        manager = RSMServerManager(
            primary_server="https://rsm.example.com",
            fallback_servers=["https://rsm-backup.example.com"]
        )

        self.assertEqual(manager.primary_server, "https://rsm.example.com")
        self.assertEqual(len(manager.fallback_servers), 1)

    def test_server_availability_check(self):
        """Test server availability checking"""
        manager = RSMServerManager(primary_server="https://rsm.example.com")

        # This will return True in the simulated implementation
        is_available, message = manager.check_server_availability(
            "https://rsm.example.com")
        self.assertTrue(is_available)

    def test_connect_with_fallback(self):
        """Test connection with fallback mechanism"""
        manager = RSMServerManager(
            primary_server="https://rsm.example.com",
            fallback_servers=["https://rsm-backup.example.com"]
        )

        # This will succeed in the simulated implementation
        result = manager.connect_with_fallback()
        self.assertTrue(result)


class TestEmergencyFunctionManager(unittest.TestCase):
    """Test main emergency function manager"""

    def setUp(self):
        """Create temporary database and manager for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.manager = EmergencyFunctionManager(
            db_type=DatabaseType.SQLITE,
            db_connection_string=self.temp_db.name
        )

    def tearDown(self):
        """Clean up resources"""
        self.manager.cleanup()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_manager_initialization(self):
        """Test emergency function manager initialization"""
        self.assertIsNotNone(self.manager.db_manager)
        self.assertIsNotNone(self.manager.rsm_manager)
        self.assertGreater(len(self.manager.regional_configs), 0)

    def test_database_initialization(self):
        """Test database initialization"""
        result = self.manager.initialize_database()
        self.assertTrue(result)

    def test_configure_emergency_profile(self):
        """Test configuring an emergency profile"""
        self.manager.initialize_database()

        result = self.manager.configure_emergency_profile(
            profile_name="test_emergency",
            region=RegionCode.US.value,
            emergency_numbers=["911"],
            psap_routing_code="TEST-PSAP-001",
            network_priority=1
        )

        self.assertTrue(result)

    def test_validate_emergency_number(self):
        """Test emergency number validation"""
        # Test US emergency number
        is_valid = self.manager.validate_emergency_number(
            "911", RegionCode.US.value)
        self.assertTrue(is_valid)

        # Test invalid number for US
        is_valid = self.manager.validate_emergency_number(
            "999", RegionCode.US.value)
        self.assertFalse(is_valid)

        # Test EU emergency number
        is_valid = self.manager.validate_emergency_number(
            "112", RegionCode.EU.value)
        self.assertTrue(is_valid)

        # Test UK emergency numbers (both 999 and 112)
        is_valid = self.manager.validate_emergency_number(
            "999", RegionCode.UK.value)
        self.assertTrue(is_valid)

        is_valid = self.manager.validate_emergency_number(
            "112", RegionCode.UK.value)
        self.assertTrue(is_valid)

    def test_get_regional_config(self):
        """Test retrieving regional configuration"""
        config = self.manager.get_regional_config(RegionCode.US.value)
        self.assertIsNotNone(config)
        self.assertEqual(config.region, RegionCode.US.value)
        self.assertIn("911", config.emergency_numbers)

    def test_provision_with_fallback(self):
        """Test provisioning with RSM fallback"""
        self.manager.initialize_database()

        config = EmergencyConfig()
        config.region = RegionCode.US.value
        config.emergency_numbers = ["911"]

        success, message = self.manager.provision_with_rsm_fallback(
            "fallback_test", config
        )

        # Should succeed either via RSM or local fallback
        self.assertTrue(success)

    def test_export_configuration(self):
        """Test exporting configuration to JSON"""
        self.manager.initialize_database()

        # Create a profile
        self.manager.configure_emergency_profile(
            profile_name="export_test",
            region=RegionCode.US.value,
            emergency_numbers=["911"]
        )

        # Export to temporary file
        temp_export = tempfile.NamedTemporaryFile(
            delete=False, suffix='.json', mode='w')
        temp_export.close()

        try:
            result = self.manager.export_configuration(
                "export_test", temp_export.name)
            self.assertTrue(result)

            # Verify file contents
            with open(temp_export.name, 'r') as f:
                exported_data = json.load(f)

            self.assertEqual(exported_data["profile_name"], "export_test")
            self.assertEqual(exported_data["region"], RegionCode.US.value)
        finally:
            if os.path.exists(temp_export.name):
                os.unlink(temp_export.name)

    def test_import_configuration(self):
        """Test importing configuration from JSON"""
        self.manager.initialize_database()

        # Create temporary import file
        temp_import = tempfile.NamedTemporaryFile(
            delete=False, suffix='.json', mode='w')
        import_data = {
            "profile_name": "import_test",
            "region": RegionCode.EU.value,
            "emergency_numbers": ["112"],
            "psap_routing_code": "EU-IMPORT-001",
            "network_priority": 1,
            "rsm_server_url": "https://rsm.example.com",
            "rsm_server_port": 443,
            "rsm_fallback_enabled": True,
            "local_cache_enabled": True,
            "alert_channels": ["SMS", "ETWS"],
            "system_codes": {"MCC": "262", "MNC": "01"}
        }

        json.dump(import_data, temp_import)
        temp_import.close()

        try:
            result = self.manager.import_configuration(temp_import.name)
            self.assertTrue(result)

            # Verify imported config
            loaded_config = self.manager.db_manager.load_emergency_config(
                "import_test")
            self.assertIsNotNone(loaded_config)
            self.assertEqual(loaded_config.region, RegionCode.EU.value)
        finally:
            if os.path.exists(temp_import.name):
                os.unlink(temp_import.name)


class TestRegionalConfigurations(unittest.TestCase):
    """Test regional emergency configurations"""

    def setUp(self):
        """Create manager with default regional configs"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.manager = EmergencyFunctionManager(
            db_type=DatabaseType.SQLITE,
            db_connection_string=self.temp_db.name
        )

    def tearDown(self):
        """Clean up resources"""
        self.manager.cleanup()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_us_configuration(self):
        """Test US emergency configuration"""
        config = self.manager.get_regional_config(RegionCode.US.value)
        self.assertIsNotNone(config)
        self.assertEqual(config.emergency_numbers, ["911"])
        self.assertIn("CMAS", config.alert_channels)

    def test_eu_configuration(self):
        """Test EU emergency configuration"""
        config = self.manager.get_regional_config(RegionCode.EU.value)
        self.assertIsNotNone(config)
        self.assertEqual(config.emergency_numbers, ["112"])
        self.assertIn("ETWS", config.alert_channels)

    def test_uk_configuration(self):
        """Test UK emergency configuration"""
        config = self.manager.get_regional_config(RegionCode.UK.value)
        self.assertIsNotNone(config)
        self.assertEqual(config.emergency_numbers, ["999", "112"])
        self.assertIn("UK-Alert", config.alert_channels)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestEmergencyConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    suite.addTests(loader.loadTestsFromTestCase(TestRSMServerManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEmergencyFunctionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestRegionalConfigurations))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("Running Emergency Functions Test Suite...")
    print("=" * 70)
    result = run_tests()
    print("=" * 70)

    if result.wasSuccessful():
        print(f"\n✓ All tests passed! ({result.testsRun} tests)")
        exit(0)
    else:
        print("\n✗ Some tests failed!")
        print(f"  Tests run: {result.testsRun}")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
        exit(1)
