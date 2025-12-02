# SQLite Database Integration for eSIM Issuance

This document describes the SQLite database integration for managing eSIM profiles with GSMA SGP.22 compliance.

## Overview

The SQLite integration provides local storage for eSIM profile data including:
- Profile IDs
- ICCIDs (Integrated Circuit Card Identifiers)
- QR code images
- Timestamps

## Architecture

The database layer consists of three main components:

1. **database.py** - Core database abstraction layer
   - `DatabaseConnection`: Connection management with context manager support
   - `GSMAComplianceDB`: CRUD operations for eSIM profile data

2. **esim_db_manager.py** - Command-line database management utility
   - Initialize database and create schema
   - Insert, retrieve, list, and export eSIM profiles
   - Validate essential eSIM variables

3. **simcard_issuer.py** - Integrated QR code generation with database storage
   - Enhanced to support optional database storage during QR generation

## Database Schema

### gsma_compliance Table

| Column      | Type     | Description                                    |
|-------------|----------|------------------------------------------------|
| id          | INTEGER  | Primary key (auto-increment)                   |
| profile_id  | TEXT     | eSIM profile identifier                        |
| iccid       | TEXT     | ICCID (19-20 digits, unique constraint)        |
| qr_code     | BLOB     | QR code image in PNG format                    |
| timestamp   | DATETIME | Auto-generated timestamp (UTC)                 |

**Indexes:**
- `idx_profile_id` on `profile_id` column
- `idx_iccid` on `iccid` column

## Usage

### 1. Initialize Database

```bash
python esim_db_manager.py init
```

This creates the `esim_gsma.db` file with the required schema.

### 2. Generate QR Code and Store in Database

```bash
python simcard_issuer.py generate-qr "sm-dp+.nexatel.com" "ACTIVATION123" \
    --save-to-db \
    --profile-id "PROF-NXT-001" \
    --output nexatel_qr.png
```

The ICCID will be auto-generated if not specified.

To specify a custom ICCID:

```bash
python simcard_issuer.py generate-qr "sm-dp+.nexatel.com" "ACTIVATION123" \
    --save-to-db \
    --profile-id "PROF-NXT-001" \
    --iccid "8901234567890123456" \
    --output nexatel_qr.png
```

### 3. Insert eSIM Data Manually

```bash
# Without QR code
python esim_db_manager.py insert "PROF-002" "8901234567890123457"

# With QR code from file
python esim_db_manager.py insert "PROF-002" "8901234567890123457" --qr-file qrcode.png
```

### 4. Retrieve Profile Information

By ICCID:
```bash
python esim_db_manager.py retrieve "8901234567890123456"
```

By record ID:
```bash
python esim_db_manager.py retrieve 1
```

### 5. List All Profiles

```bash
# List all profiles
python esim_db_manager.py list

# List with pagination
python esim_db_manager.py list --limit 50
```

### 6. Export QR Code

```bash
python esim_db_manager.py export-qr 1 output_qr.png
```

## Python API

### Basic Usage

```python
from database import DatabaseConnection, GSMAComplianceDB

# Create/connect to database
with DatabaseConnection('esim_gsma.db') as db_conn:
    gsma_db = GSMAComplianceDB(db_conn)
    
    # Create schema (first time only)
    gsma_db.create_schema()
    
    # Insert eSIM data
    record_id = gsma_db.insert_esim_data(
        profile_id='PROF-001',
        iccid='8901234567890123456',
        qr_code=qr_code_bytes  # Optional
    )
    
    # Retrieve by ICCID
    profile = gsma_db.get_profile_by_iccid('8901234567890123456')
    print(f"Profile: {profile['profile_id']}")
    
    # List all profiles
    profiles = gsma_db.get_all_profiles(limit=100)
    
    # Export QR code to file
    gsma_db.save_qr_code_to_file(record_id, 'output.png')
```

### Integration with QR Code Generation

```python
from simcard_issuer import SimCardIssuer

# Generate QR code and save to database
lpa_string = SimCardIssuer.generate_esim_qr_code(
    smdp_address='sm-dp+.nexatel.com',
    activation_code='ACTIVATION123',
    output_file='esim_qr.png',
    save_to_db=True,
    profile_id='PROF-001',
    iccid='8901234567890123456',
    db_path='esim_gsma.db'
)
```

## Data Validation

The system validates the following:

1. **Profile ID**: Cannot be empty
2. **ICCID**: 
   - Must be 19-20 digits
   - Must contain only numeric characters
   - Must be unique (enforced by database constraint)

Example validation error:
```bash
$ python esim_db_manager.py insert "PROF-001" "ABC123"
Validation errors:
  - ICCID must contain only digits
  - ICCID must be 19-20 digits (got 6)
```

## Low Coupling Design

The database layer is designed for portability:

1. **Abstraction Layer**: `DatabaseConnection` and `GSMAComplianceDB` provide clean interfaces
2. **No Direct SQL in Business Logic**: All SQL is encapsulated in the database module
3. **Type Hints**: Full type annotations for better IDE support and maintainability
4. **Context Managers**: Automatic resource cleanup

### Migrating to Other Databases

To migrate to PostgreSQL, MySQL, or other databases:

1. Implement a new connection class similar to `DatabaseConnection`
2. Update SQL syntax in `GSMAComplianceDB` methods (minimal changes needed)
3. Update connection string format

Example for PostgreSQL:
```python
import psycopg2

class PostgreSQLConnection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self):
        self.connection = psycopg2.connect(self.connection_string)
        return self.connection
    
    # ... rest of the interface
```

## Security Considerations

1. **ICCID Uniqueness**: Enforced at database level to prevent duplicates
2. **Input Validation**: ICCID format validation before database insertion
3. **BLOB Storage**: QR codes stored as binary BLOBs (not base64) for efficiency
4. **No SQL Injection**: All queries use parameterized statements

## Testing

Run the test suite:

```bash
python -m unittest test_database.py -v
```

The test suite includes:
- Connection management tests
- Schema creation validation
- CRUD operation tests
- Data validation tests
- QR code storage/retrieval tests
- Pagination tests

## File Locations

- Database file: `esim_gsma.db` (default)
- Database module: `database.py`
- Management CLI: `esim_db_manager.py`
- Tests: `test_database.py`

## Performance Considerations

1. **Indexes**: Created on `profile_id` and `iccid` for fast lookups
2. **Pagination**: Supported via `LIMIT` and `OFFSET` for large datasets
3. **Context Managers**: Ensure connections are properly closed
4. **BLOB Storage**: Efficient binary storage for QR code images

## Compliance

This implementation supports:
- **GSMA SGP.22**: eSIM activation QR code standard
- **3GPP TS 31.102**: USIM application requirements
- **ISO/IEC 7816**: Smart card standards (ICCID format)

## Troubleshooting

### Database locked error
If you encounter "database is locked" errors, ensure:
- Only one process accesses the database at a time
- Connections are properly closed (use context managers)

### ICCID validation failures
- Ensure ICCID is 19-20 digits
- Ensure ICCID contains only numeric characters
- Check for Luhn checksum validity (generated ICCIDs include this)

### QR code not found
- Verify QR code was included during insertion
- Check if file path is correct when inserting from file
- Use `list` command to verify QR code presence

## Support

For issues or questions:
1. Check this documentation
2. Review test cases in `test_database.py`
3. Check logs (INFO/ERROR level logging enabled)
