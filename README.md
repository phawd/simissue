# SIM Card Issuer with eSIM QR Code Generation

This tool provides SIM/eSIM/USIM issuance and personalization capabilities, including GSMA SGP.22 compliant eSIM QR code generation and SQLite database management for eSIM profiles.

## Features

- **Classic SIM Issuance**: Issue legacy SIM cards (3GPP TS 51.011/ETSI TS 102 221)
- **USIM Issuance**: Issue USIM/3G cards (3GPP TS 31.102)
- **eSIM Issuance**: Issue eSIM profiles (GSMA SGP.02/3GPP TS 31.102)
- **eSIM QR Code Generation**: Generate GSMA SGP.22 compliant QR codes for eSIM activation
- **SQLite Database Integration**: Store and manage eSIM profiles locally with GSMA compliance support

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

**With SQLite database storage:**
```bash
python simcard_issuer.py generate-qr "sm-dp+.nexatel.com" "NEXATEL123" \
    --save-to-db \
    --profile-id "PROF-NXT-001" \
    --output nexatel_qr.png
```

This will generate the QR code and store it in the SQLite database along with the profile ID and auto-generated ICCID.

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

## SQLite Database Management

### Initialize Database

```bash
python esim_db_manager.py init
```

### Manage eSIM Profiles

```bash
# Insert eSIM data
python esim_db_manager.py insert "PROF-001" "8901234567890123456" --qr-file qrcode.png

# Retrieve profile by ICCID
python esim_db_manager.py retrieve "8901234567890123456"

# List all profiles
python esim_db_manager.py list

# Export QR code from database
python esim_db_manager.py export-qr 1 output_qr.png
```

For detailed database documentation, see [DATABASE_GUIDE.md](DATABASE_GUIDE.md).

## Technical Details

- **QR Code Library**: Uses the `qrcode` library with PIL support
- **Error Correction**: High error correction level (ERROR_CORRECT_H) for reliable mobile scanning
- **Image Format**: PNG with 450x450 pixels (default)
- **Standards Compliance**: GSMA SGP.22 for eSIM activation codes
- **Database**: SQLite for local eSIM profile storage with GSMA compliance support
- **Low Coupling Design**: Database layer abstraction enables easy migration to other RDBMS

## References

- GSMA SGP.22: RSP Technical Specification
- 3GPP TS 31.102: USIM Application Toolkit
- 3GPP TS 51.011: Specification of the SIM
- ETSI TS 102 221: Smart Cards; UICC-Terminal interface
