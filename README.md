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

## References

- GSMA SGP.22: RSP Technical Specification
- 3GPP TS 31.102: USIM Application Toolkit
- 3GPP TS 51.011: Specification of the SIM
- ETSI TS 102 221: Smart Cards; UICC-Terminal interface
