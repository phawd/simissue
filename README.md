# SIM Card Issuer with eSIM QR Code Generation

This tool provides SIM/eSIM/USIM issuance and personalization capabilities, including GSMA SGP.22 compliant eSIM QR code generation.

## Features

- **Classic SIM Issuance**: Issue legacy SIM cards (3GPP TS 51.011/ETSI TS 102 221)
- **USIM Issuance**: Issue USIM/3G cards (3GPP TS 31.102)
- **eSIM Issuance**: Issue eSIM profiles (GSMA SGP.02/3GPP TS 31.102)
- **eSIM QR Code Generation**: Generate GSMA SGP.22 compliant QR codes for eSIM activation

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## eSIM QR Code Generation

### Standalone QR Code Generation

Generate a QR code for eSIM activation using the GSMA SGP.22 standard format:

```bash
python simcard_issuer.py generate-qr <SM-DP+ address> <activation code> [--output filename.png]
```

**Example:**
```bash
python simcard_issuer.py generate-qr "sm-dp+.example.com" "ABC123456789"
```

This will:
1. Generate a QR code image file (`esim_qr.png` by default)
2. Display the LPA activation string: `LPA:1$sm-dp+.example.com$ABC123456789`

**With custom output filename:**
```bash
python simcard_issuer.py generate-qr "sm-dp+.tmobile.com" "TMOUS12345" --output my_esim.png
```

### QR Code Generation During eSIM Issuance

Generate a QR code while issuing an eSIM profile:

```bash
python simcard_issuer.py esim-issue --emulator --generate-qr "sm-dp+.carrier.com" "ACTIVATION123"
```

This will issue the eSIM profile and automatically generate a QR code file.

## QR Code Format

The generated QR codes follow the GSMA SGP.22 standard format:

```
LPA:1$<SM-DP+ address>$<Activation Code>
```

Where:
- `LPA:1` - Indicates Local Profile Assistant protocol version 1
- `SM-DP+ address` - The Subscription Manager Data Preparation server address
- `Activation Code` - Unique activation code for the specific eSIM profile

## Usage

Users can:
1. **Scan the QR code** with their device's camera or eSIM settings
2. **Manually enter** the LPA string if QR scanning is not available

The QR code can be used on:
- iOS devices (iPhone XR and newer)
- Android devices with eSIM support
- Windows devices with eSIM capability
- Other devices supporting GSMA SGP.22 standard

## Other Commands

### Issue an eSIM
```bash
python simcard_issuer.py esim-issue [--reader N] [--emulator] [--export-android FILE]
```

### Issue a Classic SIM
```bash
python simcard_issuer.py sim-issue [--reader N] [--emulator]
```

### Issue a USIM/3G Card
```bash
python simcard_issuer.py umts-issue [--reader N] [--emulator]
```

### Set Configuration
```bash
python simcard_issuer.py set-config KEY VALUE
```

## Technical Details

- **QR Code Library**: Uses the `qrcode` library with PIL support
- **Error Correction**: High error correction level (ERROR_CORRECT_H) for reliable mobile scanning
- **Image Format**: PNG with 450x450 pixels (default)
- **Standards Compliance**: GSMA SGP.22 for eSIM activation codes

## Emergency Functions and Configuration

### Overview

The eSIM issuer now includes comprehensive emergency services functionality with extensive configurability for local area contexts. This ensures that emergency profiles can be tailored to regional requirements with robust fallback mechanisms.

### Key Features

1. **Configurable Local Area Emergency Features**
   - Regional emergency number configuration (911, 112, 999, etc.)
   - PSAP (Public Safety Answering Point) routing codes
   - System codes and alert channels (CMAS, ETWS, EU-Alert)
   - Network priority settings for emergency calls

2. **RSM Server Integration**
   - Remote SIM Management server support for profile provisioning
   - Automatic fallback to local database when RSM server is unavailable
   - Multiple fallback server support for high availability
   - Connection health monitoring and automatic failover

3. **Database Abstraction**
   - SQLite support for local testing and development
   - PostgreSQL support for production deployment
   - Seamless switching between database types
   - Local caching for offline operation

4. **Regional Compliance**
   - Pre-configured profiles for major regions (US, EU, UK, etc.)
   - Emergency number validation per region
   - Alert channel configuration per regional standards
   - MCC/MNC mapping for carrier identification

### Emergency Configuration

#### Using the Emergency Functions Module

```python
from emergency_functions import EmergencyFunctionManager, RegionCode

# Initialize manager
manager = EmergencyFunctionManager(
    db_type=DatabaseType.SQLITE,
    db_connection_string="emergency_config.db",
    rsm_server="https://rsm.example.com"
)

# Initialize database
manager.initialize_database()

# Configure US emergency profile
manager.configure_emergency_profile(
    profile_name="US_Emergency_911",
    region=RegionCode.US.value,
    emergency_numbers=["911"],
    psap_routing_code="US-PSAP-001",
    network_priority=1,
    alert_channels=["SMS", "CMAS", "WEA"]
)

# Validate emergency number
is_valid = manager.validate_emergency_number("911", RegionCode.US.value)

# Export configuration
manager.export_configuration("US_Emergency_911", "config_export.json")

# Cleanup
manager.cleanup()
```

#### Configuring Emergency Profiles via CLI

```bash
# Issue eSIM with emergency profile
python simcard_issuer.py esim-issue --emulator --emergency-profile --mode EMERGENCY --frequency b20,b28,n78

# Set emergency-specific configuration
python simcard_issuer.py set-config EMERGENCY_NUMBERS "911,112"
python simcard_issuer.py set-config PSAP_ROUTING_CODE "US-PSAP-001"
```

### RSM Server Configuration

The RSM (Remote SIM Management) server is essential for remote profile provisioning and management. Configure primary and fallback servers for high availability:

```python
from emergency_functions import RSMServerManager

# Initialize RSM manager with fallback
rsm_manager = RSMServerManager(
    primary_server="https://rsm-primary.example.com",
    fallback_servers=[
        "https://rsm-backup1.example.com",
        "https://rsm-backup2.example.com"
    ]
)

# Connect with automatic fallback
if rsm_manager.connect_with_fallback():
    print("Connected to RSM server")
else:
    print("All RSM servers unavailable - using local mode")
```

### Fallback Mechanisms

When RSM servers are temporarily unreachable, the system automatically:

1. Attempts to connect to primary RSM server
2. Falls back to secondary servers if primary is unavailable
3. Uses local SQLite/PostgreSQL database for profile storage
4. Queues operations for synchronization when servers are available
5. Logs all fallback events for audit purposes

### Regional Emergency Configurations

#### United States (911)
- **Emergency Number**: 911
- **Alert Channels**: SMS, CMAS (Commercial Mobile Alert System), WEA (Wireless Emergency Alerts)
- **MCC/MNC**: 310/260 (example)
- **PSAP Routing**: US-PSAP-XXX format

#### European Union (112)
- **Emergency Number**: 112
- **Alert Channels**: SMS, ETWS (Earthquake and Tsunami Warning System), EU-Alert
- **MCC/MNC**: Varies by country (e.g., 262/01 for Germany)
- **PSAP Routing**: EU-PSAP-XXX format

#### United Kingdom (999/112)
- **Emergency Numbers**: 999, 112
- **Alert Channels**: SMS, UK-Alert
- **MCC/MNC**: 234/15 (example)
- **PSAP Routing**: UK-PSAP-XXX format

### Database Configuration

#### SQLite (Local/Testing)

```python
from emergency_functions import EmergencyFunctionManager, DatabaseType

manager = EmergencyFunctionManager(
    db_type=DatabaseType.SQLITE,
    db_connection_string="emergency_config.db"
)
```

#### PostgreSQL (Production)

```bash
# Install PostgreSQL support
pip install psycopg2-binary
```

```python
manager = EmergencyFunctionManager(
    db_type=DatabaseType.POSTGRESQL,
    db_connection_string="postgresql://user:pass@localhost/emergency_db"
)
```

### Testing Emergency Functions

Run the comprehensive test suite:

```bash
python test_emergency_functions.py
```

The test suite covers:
- Emergency configuration creation and validation
- Database operations (SQLite and PostgreSQL)
- RSM server integration and fallback mechanisms
- Regional configuration management
- Emergency number validation
- Configuration import/export

### Example Configuration Files

#### Emergency Profile JSON

```json
{
  "profile_name": "US_Emergency_Standard",
  "region": "US",
  "emergency_numbers": ["911"],
  "psap_routing_code": "US-PSAP-001",
  "network_priority": 1,
  "rsm_server_url": "https://rsm.example.com",
  "rsm_server_port": 443,
  "rsm_fallback_enabled": true,
  "local_cache_enabled": true,
  "alert_channels": ["SMS", "CMAS", "WEA"],
  "system_codes": {
    "MCC": "310",
    "MNC": "260"
  }
}
```

### Best Practices

1. **Always Enable Fallback**: Set `rsm_fallback_enabled: true` for reliability
2. **Configure Multiple Fallback Servers**: Use at least 2 backup RSM servers
3. **Enable Local Caching**: Set `local_cache_enabled: true` for offline operation
4. **Test Regional Configurations**: Validate emergency numbers for target regions
5. **Monitor RSM Server Health**: Regularly check server availability
6. **Keep Profiles Updated**: Synchronize with RSM servers when available
7. **Audit Emergency Operations**: Review logs for compliance and debugging

### Troubleshooting

#### RSM Server Connection Issues

If RSM server connection fails:
1. Check network connectivity
2. Verify server URL and port
3. Ensure firewall allows outbound HTTPS (port 443)
4. Check server status and availability
5. System will automatically fall back to local database

#### Database Connection Issues

If database connection fails:
1. For SQLite: Check file permissions and disk space
2. For PostgreSQL: Verify connection string and credentials
3. Ensure database schema is initialized
4. Check database server status (PostgreSQL)

### Compliance Standards

The emergency functions module complies with:
- **3GPP TS 22.101**: Emergency calls
- **3GPP TS 31.102**: USIM emergency features
- **GSMA SGP.22**: RSP Technical Specification
- **NENA i3**: Emergency Services IP Network standards (US)
- **EENA NG112**: Next Generation 112 (EU)

## References

- GSMA SGP.22: RSP Technical Specification
- 3GPP TS 31.102: USIM Application Toolkit
- 3GPP TS 51.011: Specification of the SIM
- 3GPP TS 22.101: Emergency calls
- ETSI TS 102 221: Smart Cards; UICC-Terminal interface
- NENA i3: Emergency Services IP Network standards
- EENA NG112: Next Generation 112
