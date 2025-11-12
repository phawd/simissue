# Emergency Functions Developer Guide

## Overview

This guide provides comprehensive documentation for developers working with the emergency functions module in the eSIM project. The module provides configurable local area emergency features, RSM server integration, and database abstraction for emergency profile management.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Getting Started](#getting-started)
4. [Configuration Management](#configuration-management)
5. [RSM Server Integration](#rsm-server-integration)
6. [Database Operations](#database-operations)
7. [Regional Configurations](#regional-configurations)
8. [Testing](#testing)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Architecture Overview

The emergency functions module is built with a layered architecture:

```
┌─────────────────────────────────────────────────┐
│   Application Layer (simcard_issuer.py)         │
│   - CLI commands                                 │
│   - Emergency profile integration                │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│   Emergency Function Manager                     │
│   - High-level API                               │
│   - Regional configurations                      │
│   - Profile management                           │
└─────┬───────────────────────────────┬───────────┘
      │                               │
┌─────▼──────────────┐     ┌──────────▼──────────┐
│  RSM Server        │     │  Database Manager    │
│  Manager           │     │  - SQLite            │
│  - Provisioning    │     │  - PostgreSQL        │
│  - Fallback logic  │     │  - Schema management │
└────────────────────┘     └─────────────────────┘
```

## Core Components

### 1. EmergencyConfig

Data structure for emergency configuration:

```python
from emergency_functions import EmergencyConfig

config = EmergencyConfig()
config.region = "US"
config.emergency_numbers = ["911"]
config.psap_routing_code = "US-PSAP-001"
config.network_priority = 1
config.alert_channels = ["SMS", "CMAS", "WEA"]
```

### 2. EmergencyFunctionManager

Main manager for emergency operations:

```python
from emergency_functions import EmergencyFunctionManager, DatabaseType

manager = EmergencyFunctionManager(
    db_type=DatabaseType.SQLITE,
    db_connection_string="emergency_config.db",
    rsm_server="https://rsm.example.com"
)
```

### 3. DatabaseManager

Handles database operations:

```python
from emergency_functions import DatabaseManager, DatabaseType

db_manager = DatabaseManager(
    db_type=DatabaseType.SQLITE,
    connection_string="emergency_config.db"
)
db_manager.connect()
db_manager.initialize_schema()
```

### 4. RSMServerManager

Manages RSM server connections:

```python
from emergency_functions import RSMServerManager

rsm_manager = RSMServerManager(
    primary_server="https://rsm-primary.example.com",
    fallback_servers=[
        "https://rsm-backup1.example.com",
        "https://rsm-backup2.example.com"
    ]
)
```

## Getting Started

### Installation

1. Install required dependencies:

```bash
pip install -r requirements.txt
```

2. For PostgreSQL support:

```bash
pip install psycopg2-binary
```

### Basic Usage

```python
from emergency_functions import EmergencyFunctionManager, RegionCode

# Initialize manager
manager = EmergencyFunctionManager()
manager.initialize_database()

# Configure emergency profile
manager.configure_emergency_profile(
    profile_name="US_Emergency_Standard",
    region=RegionCode.US.value,
    emergency_numbers=["911"],
    psap_routing_code="US-PSAP-001",
    network_priority=1
)

# Validate emergency number
is_valid = manager.validate_emergency_number("911", RegionCode.US.value)

# Cleanup
manager.cleanup()
```

## Configuration Management

### Creating Emergency Profiles

```python
# US Emergency Profile
manager.configure_emergency_profile(
    profile_name="US_Emergency_911",
    region=RegionCode.US.value,
    emergency_numbers=["911"],
    psap_routing_code="US-PSAP-001",
    network_priority=1,
    alert_channels=["SMS", "CMAS", "WEA"]
)

# EU Emergency Profile
manager.configure_emergency_profile(
    profile_name="EU_Emergency_112",
    region=RegionCode.EU.value,
    emergency_numbers=["112"],
    psap_routing_code="EU-PSAP-112",
    network_priority=1,
    alert_channels=["SMS", "ETWS", "EU-Alert"]
)

# UK Dual Emergency Profile
manager.configure_emergency_profile(
    profile_name="UK_Emergency_Dual",
    region=RegionCode.UK.value,
    emergency_numbers=["999", "112"],
    psap_routing_code="UK-PSAP-999",
    network_priority=1,
    alert_channels=["SMS", "UK-Alert"]
)
```

### Exporting Configurations

```python
# Export to JSON
manager.export_configuration("US_Emergency_911", "us_config.json")

# Import from JSON
manager.import_configuration("us_config.json")
```

### Regional Configuration

Get pre-configured regional settings:

```python
# Get US configuration
us_config = manager.get_regional_config(RegionCode.US.value)
print(f"US Emergency Numbers: {us_config.emergency_numbers}")
print(f"US Alert Channels: {us_config.alert_channels}")

# Get EU configuration
eu_config = manager.get_regional_config(RegionCode.EU.value)
print(f"EU Emergency Numbers: {eu_config.emergency_numbers}")
```

## RSM Server Integration

### Basic RSM Operations

```python
rsm_manager = RSMServerManager(
    primary_server="https://rsm.example.com",
    fallback_servers=["https://rsm-backup.example.com"]
)

# Check server availability
is_available, message = rsm_manager.check_server_availability(
    "https://rsm.example.com"
)

# Connect with fallback
if rsm_manager.connect_with_fallback():
    print("Connected to RSM server")
else:
    print("All RSM servers unavailable")
```

### Provisioning with Fallback

```python
# Create configuration
config = EmergencyConfig()
config.region = RegionCode.US.value
config.emergency_numbers = ["911"]

# Provision with automatic fallback
success, message = manager.provision_with_rsm_fallback(
    "US_Profile_001",
    config
)

if success:
    print(f"Provisioned successfully: {message}")
else:
    print(f"Provisioning failed: {message}")
```

## Database Operations

### SQLite Configuration

```python
from emergency_functions import DatabaseManager, DatabaseType

# SQLite for local testing
db_manager = DatabaseManager(
    db_type=DatabaseType.SQLITE,
    connection_string="emergency_config.db"
)
db_manager.connect()
db_manager.initialize_schema()
```

### PostgreSQL Configuration

```python
# PostgreSQL for production
db_manager = DatabaseManager(
    db_type=DatabaseType.POSTGRESQL,
    connection_string="postgresql://user:password@localhost:5432/emergency_db"
)
db_manager.connect()
db_manager.initialize_schema()
```

### Saving and Loading Profiles

```python
# Create configuration
config = EmergencyConfig()
config.region = RegionCode.US.value
config.emergency_numbers = ["911"]

# Save to database
db_manager.save_emergency_config("US_Profile", config)

# Load from database
loaded_config = db_manager.load_emergency_config("US_Profile")
```

## Regional Configurations

### Supported Regions

| Region | Code | Emergency Numbers | Alert Channels | MCC/MNC |
|--------|------|-------------------|----------------|---------|
| United States | US | 911 | SMS, CMAS, WEA | 310/260 |
| European Union | EU | 112 | SMS, ETWS, EU-Alert | 262/01 |
| United Kingdom | UK | 999, 112 | SMS, UK-Alert | 234/15 |
| Germany | DE | 110, 112 | SMS, DE-Alert | 262/01 |
| France | FR | 15, 17, 18, 112 | SMS, FR-Alert | 208/01 |

### Adding Custom Regions

```python
# Create custom regional configuration
custom_config = EmergencyConfig()
custom_config.region = "JP"
custom_config.emergency_numbers = ["110", "119"]
custom_config.alert_channels = ["SMS", "ETWS", "J-Alert"]
custom_config.system_codes = {"MCC": "440", "MNC": "10"}

# Save configuration
manager.db_manager.save_emergency_config("JP_Emergency", custom_config)
```

## Testing

### Running the Test Suite

```bash
# Run all tests
python test_emergency_functions.py

# Run specific test class
python -m unittest test_emergency_functions.TestEmergencyConfig

# Run with verbose output
python -m unittest -v test_emergency_functions
```

### Test Coverage

The test suite covers:

- Emergency configuration creation and validation (3 tests)
- Database operations (4 tests)
- RSM server management (3 tests)
- Emergency function manager (8 tests)
- Regional configurations (3 tests)

**Total: 21 tests**

### Writing Custom Tests

```python
import unittest
from emergency_functions import EmergencyFunctionManager, RegionCode

class TestCustomFunctionality(unittest.TestCase):
    def setUp(self):
        self.manager = EmergencyFunctionManager()
        self.manager.initialize_database()
    
    def tearDown(self):
        self.manager.cleanup()
    
    def test_custom_profile(self):
        result = self.manager.configure_emergency_profile(
            profile_name="custom_test",
            region=RegionCode.US.value,
            emergency_numbers=["911"]
        )
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
```

## Best Practices

### 1. Always Enable Fallback Mechanisms

```python
# Good: Enable fallback
config.rsm_fallback_enabled = True
config.local_cache_enabled = True

# Bad: Disable fallback (only for testing)
config.rsm_fallback_enabled = False
```

### 2. Use Multiple RSM Servers

```python
# Good: Multiple fallback servers
rsm_manager = RSMServerManager(
    primary_server="https://rsm-primary.example.com",
    fallback_servers=[
        "https://rsm-backup1.example.com",
        "https://rsm-backup2.example.com"
    ]
)

# Bad: Single server (no redundancy)
rsm_manager = RSMServerManager(
    primary_server="https://rsm.example.com"
)
```

### 3. Validate Emergency Numbers

```python
# Always validate before saving
if manager.validate_emergency_number("911", RegionCode.US.value):
    manager.configure_emergency_profile(...)
else:
    print("Invalid emergency number for region")
```

### 4. Use Context Managers

```python
# Good: Proper cleanup
try:
    manager = EmergencyFunctionManager()
    manager.initialize_database()
    # ... operations ...
finally:
    manager.cleanup()
```

### 5. Handle Exceptions

```python
try:
    manager.configure_emergency_profile(
        profile_name="test",
        region=RegionCode.US.value,
        emergency_numbers=["911"]
    )
except Exception as e:
    print(f"Configuration failed: {e}")
    # Handle error appropriately
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Fails

**Problem**: `Failed to connect to database`

**Solution**:
- For SQLite: Check file permissions and disk space
- For PostgreSQL: Verify connection string and credentials
- Ensure database server is running

```python
# Check connection
if db_manager.connect():
    print("Connected successfully")
else:
    print("Connection failed - check logs")
```

#### 2. RSM Server Unavailable

**Problem**: `All RSM servers unavailable`

**Solution**:
- Check network connectivity
- Verify firewall settings (allow HTTPS/443)
- Enable fallback to local database
- Check server status

```python
# Test server availability
is_available, message = rsm_manager.check_server_availability(server_url)
print(f"Server status: {message}")
```

#### 3. Import Error for PostgreSQL

**Problem**: `PostgreSQL support requires psycopg2`

**Solution**:
```bash
pip install psycopg2-binary
```

#### 4. Invalid Emergency Number

**Problem**: Emergency number not recognized

**Solution**:
- Verify region code is correct
- Check regional configuration
- Ensure number is in approved list

```python
# Debug regional config
config = manager.get_regional_config(region)
print(f"Valid numbers: {config.emergency_numbers}")
```

### Logging

Enable detailed logging for debugging:

```python
import logging

# Set logging level
logging.basicConfig(level=logging.DEBUG)

# Now all operations will produce detailed logs
manager = EmergencyFunctionManager()
```

### Debug Mode

```python
# Enable verbose output
import emergency_functions
emergency_functions.logger.setLevel(logging.DEBUG)

# Run operations - detailed logs will be printed
```

## API Reference

### EmergencyFunctionManager

**Methods**:

- `__init__(db_type, db_connection_string, rsm_server)`: Initialize manager
- `initialize_database()`: Set up database schema
- `configure_emergency_profile(...)`: Create emergency profile
- `validate_emergency_number(number, region)`: Validate emergency number
- `get_regional_config(region)`: Get regional configuration
- `provision_with_rsm_fallback(profile_name, config)`: Provision with fallback
- `export_configuration(profile_name, output_file)`: Export to JSON
- `import_configuration(input_file)`: Import from JSON
- `cleanup()`: Close connections and cleanup resources

### EmergencyConfig

**Attributes**:

- `region`: Regional code (US, EU, UK, etc.)
- `emergency_numbers`: List of emergency numbers
- `psap_routing_code`: PSAP routing code
- `network_priority`: Priority level (1-5, 1=highest)
- `rsm_server_url`: RSM server URL
- `rsm_server_port`: RSM server port
- `rsm_fallback_enabled`: Enable fallback
- `local_cache_enabled`: Enable local caching
- `alert_channels`: List of alert channels
- `system_codes`: Dictionary of system codes

**Methods**:

- `to_dict()`: Convert to dictionary
- `from_dict(data)`: Create from dictionary

## Standards Compliance

The emergency functions module complies with:

- **3GPP TS 22.101**: Service aspects; Service principles (Emergency calls)
- **3GPP TS 31.102**: USIM Application Toolkit characteristics
- **GSMA SGP.22**: RSP Technical Specification
- **NENA i3**: Emergency Services IP Network (US)
- **EENA NG112**: Next Generation 112 (EU)
- **ETSI TS 102 221**: Smart Cards; UICC-Terminal interface

## Contributing

When contributing to the emergency functions module:

1. Follow PEP 8 style guidelines
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure backward compatibility
5. Run linting: `flake8 emergency_functions.py`
6. Run tests: `python test_emergency_functions.py`

## Support

For issues or questions:

1. Check this guide and README.md
2. Review test cases for usage examples
3. Check module logs for error details
4. Verify standards compliance requirements
5. Consult 3GPP/GSMA specifications

## Version History

- **v1.0.0** (2025-11-12): Initial release
  - Emergency profile configuration
  - RSM server integration with fallback
  - Database abstraction (SQLite/PostgreSQL)
  - Regional configurations (US, EU, UK)
  - Comprehensive test suite (21 tests)
  - Full documentation

## License

See main project LICENSE file.
