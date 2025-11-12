# Standard library imports
import datetime
import os
import sys
import json
import base64
import random
import subprocess
# External library imports
try:
    from smartcard.util import toHexString
    from smartcard.System import readers
except ImportError:
    toHexString = None
    readers = None

try:
    import qrcode
except ImportError:
    qrcode = None

# Set these according to the SIM profile, carrier, and device requirements.
#
# Signal Power Control:
# You may set signal power (in dBm) for test/dev or compliance:
#   python simcard_issuer.py set-config SIGNAL_POWER "23"
#   python simcard_issuer.py esim-issue --signal-power 20
# This value is logged and exported for operator/carrier traceability, but not enforced by the tool.
# Typical values: 23dBm (standard max for LTE UE), 20dBm (reduced), 10dBm (test/low power).
#
# FREQUENCY and MODE Controls (International/Carrier Configurable)
# This tool supports operator-configurable FREQUENCY and MODE settings for SIM/eSIM/USIM issuance. These parameters are essential for compliance with international and carrier-specific requirements (e.g., 2G/3G/4G/5G, region bands, test/production modes).

# ----------------------------------
# --frequency accepts MHz, band code, or NR code. The tool does not enforce, but logs and exports for compliance.
# --mode should match the technology (GSM, UMTS, LTE, 5G) for the carrier/region.
# Set these according to the SIM profile, carrier, and device requirements.
#
# Signal Power Control:
# ---------------------
# You may set signal power (in dBm) for test/dev or compliance:
#   python simcard_issuer.py set-config SIGNAL_POWER "23"
#   python simcard_issuer.py esim-issue --signal-power 20
# This value is logged and exported for operator/carrier traceability, but not enforced by the tool.
# Typical values: 23dBm (standard max for LTE UE), 20dBm (reduced), 10dBm (test/low power).
#
# FREQUENCY and MODE Controls (International/Carrier Configurable)
# --------------------------------------------------------------
# This tool supports operator-configurable FREQUENCY and MODE settings for SIM/eSIM/USIM issuance. These parameters are essential for compliance with international and carrier-specific requirements (e.g., 2G/3G/4G/5G, region bands, test/production modes).

# FREQUENCY: Specifies the radio frequency band or profile (e.g., '900MHz', '1800MHz', '850MHz', '1900MHz', '2100MHz', '2600MHz', 'NR', 'ALL').
# MODE: Specifies the operational mode (e.g., 'GSM', 'UMTS', 'LTE', '5G', 'TEST', 'PRODUCTION').


# ...existing code...
# The following block was previously a markdown/documentation string and is now commented out for valid Python syntax.
# ==============================
# PCSC SIM/eSIM Issuer Tool - Operator CLI & Function Documentation
# ==============================
#
# This tool provides a full-featured, standards-based SIM/eSIM/USIM issuer and personalization suite.
# All commands, options, and functions are documented for operator clarity and compliance.
#
# ------------------------------
# CLI Commands (with usage examples)
# ------------------------------
#
# 1. Issue an eSIM (GSMA SGP.02/3GPP TS 31.102):
#    # Issue an eSIM profile, optionally export for Android
#    python simcard_issuer.py esim-issue [--reader N] [--emulator] [--export-android FILE] [--frequency BANDS] [--mode MODE] [--signal-power DBM] [--emergency-profile]
#    - --reader N: Select PCSC reader index (default 0)
#    - --emulator: Run in emulator mode (no real card required)
#    - --export-android FILE: Export config for Android eSIM import (writes JSON)
#    - --frequency: Comma-separated bands (e.g., b20,b28,n78) or MHz (e.g., 2100MHz)
#    - --mode: Technology (GSM, UMTS, LTE, 5G, EMERGENCY, etc.)
#    - --signal-power: Set signal power in dBm (e.g., 23)
#    - --emergency-profile: Mark profile for emergency services only (911/112/PSAP)
#
# 2. Issue a classic SIM (3GPP TS 51.011/ETSI TS 102 221):
#    # Issue a legacy/classic SIM profile
#    python simcard_issuer.py sim-issue [--reader N] [--emulator] [--frequency BANDS] [--mode MODE] [--signal-power DBM] [--emergency-profile]
#    - Same options as esim-issue
#
# 3. Issue a USIM/3G card (3GPP TS 31.102):
#    # Issue a USIM/3G profile
#    python simcard_issuer.py umts-issue [--reader N] [--emulator] [--frequency BANDS] [--mode MODE] [--signal-power DBM] [--emergency-profile]
#    - Same options as esim-issue
#
# 4. Set a configuration value:
#    # Set a config value for personalization (IMSI, Ki, OPc, SPN, etc.)
#    python simcard_issuer.py set-config KEY VALUE
#    - KEY: IMSI, Ki, OPc, SPN, CERT, PRIVKEY, FREQUENCY, MODE, SIGNAL_POWER, etc.
#    - VALUE: Value to set (see documentation for format)
#
# ------------------------------
# Python API Functions (for advanced/automated use)
# ------------------------------
#
# SimCardIssuer.import_keys_for_carrier(carrier_name)
#     # Import all needed keys for a given carrier (loads Ki, OPc, CERT, PRIVKEY from files)
#     # Usage: Only from Python, not CLI. Example: issuer.import_keys_for_carrier('T-Mobile US')
#
# SimCardIssuer.generate_random_key(length=16)
#     # Generate a random cryptographic key (hex string) for test/dev
#     # Usage: Only from Python, not CLI. Example: SimCardIssuer.generate_random_key(16)
#
# ------------------------------
# Command/Function Comments (Plain English)
# ------------------------------
#
# Every function and APDU command is commented in plain English, describing its purpose, usage, and any restrictions. See code for details.
#
# ------------------------------
# Examples
# ------------------------------
# python simcard_issuer.py esim-issue --emulator --export-android esim_profile.json
# python simcard_issuer.py sim-issue --reader 1 --frequency b20,b28,n78 --mode LTE --signal-power 23
# python simcard_issuer.py set-config IMSI "31 02 60 12 34 56 78 90 12 34 56 78 90 12 34"
# python simcard_issuer.py esim-issue --emulator --frequency b20,b28,n78 --mode EMERGENCY --emergency-profile
#
# ------------------------------
# Function Usage/Restrictions
# ------------------------------
# * Only use import_keys_for_carrier and generate_random_key from Python, not CLI.
# * All CLI commands are safe for operator use and log every action.
# * Emulator mode is for testing only; use a real card for production.
#
# ------------------------------
# All APDU commands and flows are commented in the code for operator understanding.
# ------------------------------
class SimCardIssuer:
    # This class provides all SIM/eSIM/USIM issuance, personalization, and key management logic.
    # Use via CLI for normal operation, or via Python API for automation/advanced use.

    @staticmethod
    def generate_random_key(length=16):
        # Generate a random cryptographic key (hex string) for test/dev. Not for production use.
        # Only use from Python, not CLI.
        import secrets
        key_bytes = secrets.token_bytes(length)
        # Return as space-separated hex string for config compatibility
        return ' '.join(f"{b:02X}" for b in key_bytes)
    # Keyset file references for configuration (used for carrier/cert personalization)
    KEYSET_FILES = {
        "Ki": "tmo_ki.hex",         # File with hex string for Ki (subscriber authentication key)
        "OPc": "tmo_opc.hex",       # File with hex string for OPc (operator variant key)
        "CERT": "tmo_cert.der",     # DER-encoded carrier certificate
        "PRIVKEY": "tmo_privkey.pem" # PEM-encoded private key (for eSIM)
    }

    # Enumerate options for other US and European carriers and their key kits
    CARRIER_KEY_KITS = {
        # US Carriers
        "T-Mobile US": {
            "MCCMNC": "310260",
            "Ki_file": "tmo_ki.hex",
            "OPc_file": "tmo_opc.hex",
            "CERT_file": "tmo_cert.der",
            "PRIVKEY_file": "tmo_privkey.pem"
        },
        "AT&T": {
            "MCCMNC": "310410",
            "Ki_file": "att_ki.hex",
            "OPc_file": "att_opc.hex",
            "CERT_file": "att_cert.der",
            "PRIVKEY_file": "att_privkey.pem"
        },
        "Verizon": {
            "MCCMNC": "311480",
            "Ki_file": "vz_ki.hex",
            "OPc_file": "vz_opc.hex",
            "CERT_file": "vz_cert.der",
            "PRIVKEY_file": "vz_privkey.pem"
        },
        # European Carriers
        "Vodafone UK": {
            "MCCMNC": "23415",
            "Ki_file": "vfuk_ki.hex",
            "OPc_file": "vfuk_opc.hex",
            "CERT_file": "vfuk_cert.der",
            "PRIVKEY_file": "vfuk_privkey.pem"
        },
        "Deutsche Telekom": {
            "MCCMNC": "26201",
            "Ki_file": "dt_ki.hex",
            "OPc_file": "dt_opc.hex",
            "CERT_file": "dt_cert.der",
            "PRIVKEY_file": "dt_privkey.pem"
        },
        "Orange France": {
            "MCCMNC": "20801",
            "Ki_file": "orange_ki.hex",
            "OPc_file": "orange_opc.hex",
            "CERT_file": "orange_cert.der",
            "PRIVKEY_file": "orange_privkey.pem"
        },
        # Add more as needed
    }

    def sim_apdu_mode(self, emulator=False):
        # Classic SIM personalization flow for legacy GSM SIMs.
        # Implements 3GPP TS 51.011 and ETSI TS 102 221.
        # Operator is guided through file selection and update for IMSI, Kc, SPN, etc.
        self.log("--- Classic SIM Personalization (3GPP TS 51.011/ETSI TS 102 221) ---")
        sim_apdus = [
            # Select MF (Master File)
            ([0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], "Select MF (Master File)"),
            # Select DF_GSM (GSM Directory)
            ([0x00, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x20], "Select DF_GSM (GSM Directory)"),
            # Select EF_IMSI (IMSI file)
            ([0x00, 0xA4, 0x02, 0x00, 0x02, 0x6F, 0x07], "Select EF_IMSI"),
            # Read Binary (IMSI)
            ([0x00, 0xB0, 0x00, 0x00, 0x09], "Read Binary (IMSI)"),
            # Update Binary (IMSI, example value)
            ([0x00, 0xD6, 0x00, 0x00, 0x09] + [0x21, 0x43, 0x65, 0x87, 0x09, 0x21, 0x43, 0x65, 0xF9], "Update Binary (IMSI example)"),
            # Select EF_Kc (Ciphering Key)
            ([0x00, 0xA4, 0x02, 0x00, 0x02, 0x6F, 0x20], "Select EF_Kc (Ciphering Key)"),
            # Update Binary (Kc, example value)
            ([0x00, 0xD6, 0x00, 0x00, 0x09] + [0xAA]*9, "Update Binary (Kc example)"),
            # Select EF_SPN (Service Provider Name)
            ([0x00, 0xA4, 0x02, 0x00, 0x02, 0x6F, 0x46], "Select EF_SPN (Service Provider Name)"),
            # Update Binary (SPN: T-Mobile US MVN)
            ([0x00, 0xD6, 0x00, 0x00, 0x0F] + [0x54, 0x2D, 0x4D, 0x6F, 0x62, 0x69, 0x6C, 0x65, 0x20, 0x55, 0x53, 0x20, 0x4D, 0x56, 0x4E], "Update Binary (SPN: T-Mobile US MVN)")
        ]
        for apdu, desc in sim_apdus:
            self.send_apdu(apdu, desc, emulator=emulator)
        self.log("--- Classic SIM Personalization Complete ---")

    def umts_apdu_mode(self, emulator=False):
        # UMTS/USIM personalization flow for 3G/4G/5G USIM cards.
        # Implements 3GPP TS 31.102. Operator is guided through file selection and update for IMSI, AD, authentication, etc.
        self.log("--- UMTS/USIM Personalization (3GPP TS 31.102/Legacy 3G) ---")
        umts_apdus = [
            # Select MF (Master File)
            ([0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], "Select MF (Master File)"),
            # Select DF_USIM (USIM Directory)
            ([0x00, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0xFF], "Select DF_USIM (USIM Directory)"),
            # Select EF_IMSI (IMSI file)
            ([0x00, 0xA4, 0x02, 0x00, 0x02, 0x6F, 0x07], "Select EF_IMSI (USIM)"),
            # Update Binary (IMSI, example value)
            ([0x00, 0xD6, 0x00, 0x00, 0x09] + [0x21, 0x43, 0x65, 0x87, 0x09, 0x21, 0x43, 0x65, 0xF9], "Update Binary (IMSI example)"),
            # Select EF_AD (Administrative Data)
            ([0x00, 0xA4, 0x02, 0x00, 0x02, 0x6F, 0xAD], "Select EF_AD (Administrative Data)"),
            # Update Binary (AD, example value)
            ([0x00, 0xD6, 0x00, 0x00, 0x04] + [0x00, 0x00, 0x00, 0x00], "Update Binary (AD example)"),
            # Select EF_USIM_AUTH (Authentication)
            ([0x00, 0xA4, 0x02, 0x00, 0x02, 0x6F, 0x20], "Select EF_USIM_AUTH (Authentication)"),
            # RUN UMTS ALGORITHM (3G Auth, RAND/AUTN)
            ([0x00, 0x88, 0x00, 0x81, 0x20] + [0x02]*16 + [0x03]*16, "RUN UMTS ALGORITHM (3G Auth, RAND=0x02.., AUTN=0x03..)")
        ]
        for apdu, desc in umts_apdus:
            self.send_apdu(apdu, desc, emulator=emulator)
        self.log("--- UMTS/USIM Personalization Complete ---")
    @staticmethod
    def generate_imsi(mcc="310", mnc="260"):
        # Generate a random 15-digit IMSI with given MCC/MNC. Used for test/dev.
        # Generate a random 15-digit IMSI with given MCC/MNC
        msin = ''.join(str(random.randint(0, 9)) for _ in range(15 - len(mcc + mnc)))
        return mcc + mnc + msin

    @staticmethod
    def generate_imei():
        # Generate a random 15-digit IMEI (Luhn check digit). Used for test/dev.
        # Generate a random 15-digit IMEI (Luhn check digit)
        imei_base = [random.randint(0, 9) for _ in range(14)]
        def luhn_checksum(digits):
            s = 0
            for i, d in enumerate(digits[::-1]):
                if i % 2 == 0:
                    d2 = d * 2
                    s += d2 if d2 < 10 else d2 - 9
                else:
                    s += d
            return (10 - (s % 10)) % 10
        check = luhn_checksum(imei_base)
        return ''.join(str(d) for d in imei_base) + str(check)

    @staticmethod
    def generate_iccid(issuer_id="89", country_code="01", issuer_code="234"):
        # Generate a random 19-digit ICCID with Luhn check digit
        # Format: II CC IIII NNNNNNNNNN C
        # II = Issuer Identifier (89 for telecom)
        # CC = Country Code
        # IIII = Issuer Code
        # NNNNNNNNNN = Account Number (10 digits)
        # C = Check digit (Luhn)
        account_number = ''.join(str(random.randint(0, 9)) for _ in range(10))
        iccid_base = issuer_id + country_code + issuer_code + account_number

        # Calculate Luhn check digit
        def luhn_checksum(number_str):
            digits = [int(d) for d in number_str]
            s = 0
            for i, d in enumerate(digits[::-1]):
                if i % 2 == 0:
                    d2 = d * 2
                    s += d2 if d2 < 10 else d2 - 9
                else:
                    s += d
            return (10 - (s % 10)) % 10

        check = luhn_checksum(iccid_base)
        return iccid_base + str(check)

    @staticmethod
    def generate_lpa_string(smdp_address, activation_code):
        # Generate GSMA SGP.22 compliant LPA activation string
        # Format: LPA:1$<SM-DP+ address>$<Activation Code>
        # This string can be used for manual entry or QR code generation
        return f"LPA:1${smdp_address}${activation_code}"

    @staticmethod
    def generate_esim_qr_code(smdp_address, activation_code, output_file="esim_qr.png",
                             save_to_db=False, profile_id=None, iccid=None, db_path="esim_gsma.db"):
        # Generate a QR code for eSIM activation per GSMA SGP.22 standard
        # The QR code encodes the LPA string: LPA:1$<SM-DP+ address>$<Activation Code>
        #
        # Args:
        #   smdp_address: SM-DP+ server address (e.g., "sm-dp+.example.com")
        #   activation_code: Unique activation code for the eSIM profile
        #   output_file: Output filename for the QR code image (default: "esim_qr.png")
        #   save_to_db: If True, save QR code to SQLite database (default: False)
        #   profile_id: eSIM profile identifier (required if save_to_db is True)
        #   iccid: Integrated Circuit Card Identifier (required if save_to_db is True)
        #   db_path: Path to SQLite database (default: "esim_gsma.db")
        #
        # Returns:
        #   The LPA string that was encoded in the QR code
        if qrcode is None:
            raise ImportError("qrcode library is required. Install with: pip install qrcode[pil]")

        lpa_string = SimCardIssuer.generate_lpa_string(smdp_address, activation_code)

        # Generate QR code with good error correction for mobile scanning
        qr = qrcode.QRCode(
            version=1,  # Auto-adjust version based on data
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=10,
            border=4,
        )
        qr.add_data(lpa_string)
        qr.make(fit=True)

        # Create and save the image
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_file)

        # Save to database if requested
        if save_to_db:
            if not profile_id or not iccid:
                raise ValueError("profile_id and iccid are required when save_to_db is True")

            try:
                from database import DatabaseConnection, GSMAComplianceDB

                # Read QR code file as binary
                with open(output_file, 'rb') as f:
                    qr_code_data = f.read()

                # Save to database
                with DatabaseConnection(db_path) as db_conn:
                    gsma_db = GSMAComplianceDB(db_conn)
                    record_id = gsma_db.insert_esim_data(profile_id, iccid, qr_code_data)
                    print(f"[Database] Saved eSIM data to database: Record ID {record_id}")
            except Exception as e:
                print(f"[Database] Warning: Failed to save to database: {e}")

        return lpa_string

    # Configuration and log filenames
    CONFIG_FILE = "simcard_issuer_config.json"
    LOG_FILE = "simcard_issuer_log.txt"

    def __init__(self):
        self.reader = None
        self.connection = None
        self.config = self.load_config()

    def load_config(self):
        # Load the configuration from disk (JSON file). Used for personalization values.
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as f:
                try:
                    return json.load(f)
                except Exception:
                    return {}
        return {}

    def save_config(self):
        # Save the current configuration to disk (JSON file).
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def list_readers(self):
        # List all available PCSC smart card readers.
        r = readers()
        if not r:
            print("No PCSC readers found.")
            return []
        print("Available readers:")
        for idx, reader in enumerate(r):
            print(f"[{idx}] {reader}")
        return r

    def connect(self, reader_idx=0):
        # Connect to the selected PCSC smart card reader.
        r = readers()
        if not r:
            print("No PCSC readers available.")
            return False
        try:
            self.reader = r[reader_idx]
            self.connection = self.reader.createConnection()
            self.connection.connect()
            print(f"Connected to {self.reader}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def log(self, message):
        # Log a message to file and print to console, with timestamp.
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        with open(self.LOG_FILE, 'a') as f:
            f.write(log_entry)
        print(log_entry, end="")

    def send_apdu(self, apdu, description=None, emulator=False):
        # Send an APDU command to the card (or emulator), with operator-facing description.
        # All APDUs are commented in plain English in the code.
        apdu_str = toHexString(apdu)
        if description:
            self.log(f"Sending APDU ({description}): {apdu_str}")
        else:
            self.log(f"Sending APDU: {apdu_str}")
        if emulator:
            # Simulate a generic successful response (SW=0x9000)
            data = [0x90, 0x00]
            sw1, sw2 = 0x90, 0x00
            self.log(f"[EMULATOR] Simulated Response: {toHexString(data)}, SW: {sw1:02X} {sw2:02X}")
            return data, sw1, sw2
        if not self.connection:
            self.log("Not connected to a card.")
            return None
        try:
            data, sw1, sw2 = self.connection.transmit(apdu)
            resp_str = toHexString(data)
            self.log(f"Received Response: {resp_str}, SW: {sw1:02X} {sw2:02X}")
            return data, sw1, sw2
        except Exception as e:
            self.log(f"APDU transmit failed: {e}")
            return None

    def issuer_mode(self, emulator=False, export_android=None):
        # Main eSIM/pSIM personalization flow (GSMA SGP.02, 3GPP TS 31.102, T-Mobile MVNO, etc.)
        # Handles all APDU commands, config, logging, and Android export.
        # Operator is guided at every step. See logs for details.
        print("\n[Issuer Mode] - eSIM/pSIM Personalization Start")
        print(f"Loaded config: {json.dumps(self.config, indent=2)}")
        self.log("--- Starting Personalization Session ---")

        # --- ETSI TS 102 221: Encryption and Security Operations ---
        # This section covers all encryption types and security operations supported by the standard.
        # Each APDU is commented with its cryptographic context and operator-facing description.
        # Note: Real cryptographic values must be generated securely in production.

        apdu_sequence = [
            # --- MF (Master File) commands ---
            # Select MF
            ([0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], "Select MF (Master File)"),
            # Get Response (after select, to get FCI)
            ([0x00, 0xC0, 0x00, 0x00, 0x0F], "Get Response (FCI for MF)"),
            # Read Binary (read first 10 bytes of MF)
            ([0x00, 0xB0, 0x00, 0x00, 0x0A], "Read Binary (first 10 bytes of MF)"),
            # Update Binary (write 2 bytes to MF at offset 0)
            ([0x00, 0xD6, 0x00, 0x00, 0x02, 0x12, 0x34], "Update Binary (write 2 bytes to MF at offset 0)"),
            # Verify CHV1 (PIN1, default 8x'FF')
            ([0x00, 0x20, 0x00, 0x01, 0x08, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], "Verify CHV1 (PIN1, default)"),
            # Change CHV1 (PIN1)
            ([0x00, 0x24, 0x00, 0x01, 0x10] + [0xFF]*8 + [0x12]*8, "Change CHV1 (PIN1, old=FF, new=12)"),
            # Disable CHV1
            ([0x00, 0x26, 0x00, 0x01, 0x08] + [0x12]*8, "Disable CHV1 (PIN1=12)"),
            # Enable CHV1
            ([0x00, 0x28, 0x00, 0x01, 0x08] + [0x12]*8, "Enable CHV1 (PIN1=12)"),
            # Get CHV Status
            ([0x00, 0x4D, 0x00, 0x01, 0x00], "Get CHV Status (MF)"),

            # --- DF_GSM (GSM Directory) commands ---
            # Select DF_GSM
            ([0x00, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x20], "Select DF_GSM (GSM Directory)"),
            # Get Response (after select, to get FCI)
            ([0x00, 0xC0, 0x00, 0x00, 0x0F], "Get Response (FCI for DF_GSM)"),
            # Read Binary (read first 10 bytes of DF_GSM)
            ([0x00, 0xB0, 0x00, 0x00, 0x0A], "Read Binary (first 10 bytes of DF_GSM)"),
            # Update Binary (write 2 bytes to DF_GSM at offset 0)
            ([0x00, 0xD6, 0x00, 0x00, 0x02, 0x56, 0x78], "Update Binary (write 2 bytes to DF_GSM at offset 0)"),
            # Status (get status of DF_GSM)
            ([0x00, 0xF2, 0x00, 0x00, 0x00], "Status (DF_GSM)"),
            # Manage Channel (open)
            ([0x00, 0x70, 0x00, 0x00, 0x01, 0x01], "Manage Channel (open)"),
            # Manage Channel (close)
            ([0x00, 0x70, 0x80, 0x00, 0x00], "Manage Channel (close)"),

            # --- Encryption and Authentication Operations ---
            # RUN GSM ALGORITHM (2G authentication, returns SRES/Kc, uses Ki)
            #   CLA=00 INS=88 P1=00 P2=00 Lc=10 Data=RAND (random challenge)
            ([0x00, 0x88, 0x00, 0x00, 0x10] + [0x01]*16, "RUN GSM ALGORITHM (2G Auth, RAND=0x01..0x10)"),

            # RUN UMTS ALGORITHM (3G authentication, returns RES/CK/IK, uses Ki/OPc)
            #   CLA=00 INS=88 P1=00 P2=81 Lc=20 Data=RAND(16)+AUTN(16)
            ([0x00, 0x88, 0x00, 0x81, 0x20] + [0x02]*16 + [0x03]*16, "RUN UMTS ALGORITHM (3G Auth, RAND=0x02.., AUTN=0x03..)") ,

            # INTERNAL AUTHENTICATE (ISO 7816-4, generic challenge/response)
            #   CLA=00 INS=88 P1=00 P2=00 Lc=08 Data=challenge
            ([0x00, 0x88, 0x00, 0x00, 0x08] + [0x04]*8, "INTERNAL AUTHENTICATE (ISO 7816-4, challenge=0x04..)") ,

            # EXTERNAL AUTHENTICATE (ISO 7816-4, generic)
            #   CLA=00 INS=82 P1=00 P2=00 Lc=08 Data=cryptogram
            ([0x00, 0x82, 0x00, 0x00, 0x08] + [0x05]*8, "EXTERNAL AUTHENTICATE (ISO 7816-4, cryptogram=0x05..)") ,

            # INCREASE (increment a counter, e.g. EF_ADM)
            #   CLA=00 INS=32 P1=00 P2=00 Lc=02 Data=MSB,LSB
            ([0x00, 0x32, 0x00, 0x00, 0x02, 0x00, 0x01], "INCREASE (increment counter by 1)") ,

            # GET CHALLENGE (retrieve random for session key or challenge)
            #   CLA=00 INS=84 P1=00 P2=00 Le=08
            ([0x00, 0x84, 0x00, 0x00, 0x08], "GET CHALLENGE (get random 8 bytes)") ,

            # VERIFY (PIN/CHV with secure messaging, if enabled)
            #   Secure messaging is handled at a higher layer, but operator is informed here
            #   (APDU structure is the same as normal VERIFY, but data is encrypted)
            #   Example below is a placeholder for secure messaging
            ([0x0C, 0x20, 0x00, 0x01, 0x08] + [0xAA]*8, "VERIFY (PIN1, secure messaging, encrypted)") ,
        ]

        # Iterate through all MF, DF_GSM, and encryption APDUs, operator sees each action
        for apdu, desc in apdu_sequence:
            self.send_apdu(apdu, desc, emulator=emulator)

        # --- GSMA SGP.02 eSIM (eUICC) Personalization Sequence ---
        # See GSMA SGP.02 v4.0, 3GPP TS 31.102, and GlobalPlatform Card Spec
        # Each step is commented and can be adapted for your SM-DP/SM-DS implementation

        # 1. SELECT ISD-P (Issuer Security Domain - Profile)
        #   AID for ISD-P is typically A0000005591010... (varies by vendor)
        select_isdp = [0x00, 0xA4, 0x04, 0x00, 0x08, 0xA0, 0x00, 0x00, 0x05, 0x59, 0x10, 0x10, 0xFF]
        self.send_apdu(select_isdp, "GSMA SGP.02: Select ISD-P (Issuer Security Domain)", emulator=emulator)

        # 2. INITIALIZE UPDATE (GlobalPlatform SCP03)
        #   Host initiates secure channel session
        #   Host challenge (8 bytes) is random; here we use a placeholder
        #   CLA=80 INS=50 P1=00 P2=00 Lc=08 Data=host_challenge
        host_challenge = [0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08]  # Example only
        init_update = [0x80, 0x50, 0x00, 0x00, 0x08] + host_challenge
        self.send_apdu(init_update, "GSMA SGP.02: INITIALIZE UPDATE (SCP03)", emulator=emulator)

        # 3. EXTERNAL AUTHENTICATE (GlobalPlatform SCP03)
        #   Host proves knowledge of session keys (cryptogram)
        #   CLA=84 INS=82 P1=00 P2=00 Lc=10 Data=cryptogram (placeholder)
        cryptogram = [0xAA]*16  # Example only
        ext_auth = [0x84, 0x82, 0x00, 0x00, 0x10] + cryptogram
        self.send_apdu(ext_auth, "GSMA SGP.02: EXTERNAL AUTHENTICATE (SCP03)", emulator=emulator)

        # 4. STORE DATA (Profile Download)
        #   Used to load profile data (e.g., profile metadata, ISD-P params)
        #   CLA=80 INS=E2 P1=00 P2=00 Lc=xx Data=TLV (profile chunk)
        #   This is typically done in multiple chunks; here is a placeholder
        profile_chunk = [0x5A, 0x04, 0x11, 0x22, 0x33, 0x44]  # Example TLV
        store_data = [0x80, 0xE2, 0x00, 0x00, len(profile_chunk)] + profile_chunk
        self.send_apdu(store_data, "GSMA SGP.02: STORE DATA (Profile Chunk)", emulator=emulator)

        # 5. INSTALL [for install profile or applet]
        #   CLA=80 INS=E6 P1=02 P2=00 Lc=xx Data=TLV (install params)
        install_params = [0xC9, 0x01, 0x01]  # Example TLV
        install_apdu = [0x80, 0xE6, 0x02, 0x00, len(install_params)] + install_params
        self.send_apdu(install_apdu, "GSMA SGP.02: INSTALL (Profile/Applet)", emulator=emulator)

        # 6. GET STATUS (optional, to verify install)
        #   CLA=80 INS=F2 P1=00 P2=00 Lc=00
        get_status = [0x80, 0xF2, 0x00, 0x00, 0x00]
        self.send_apdu(get_status, "GSMA SGP.02: GET STATUS (Verify Profile)", emulator=emulator)

        # Note: In production, all cryptographic values must be generated securely and profile data must be constructed per GSMA SGP.02 and carrier requirements.

        # --- T-Mobile MVNO Personalization Logic ---
        # This section enforces T-Mobile US MVNO requirements for SIM/eSIM issuance.
        # File IDs and personalization steps per 3GPP TS 51.011 and T-Mobile US guidelines.
        # Operator is guided at each step.

        tmo_files = {
            "ICCID": [0x2F, 0xE2],  # EF_ICCID
            "IMSI": [0x6F, 0x07],   # EF_IMSI
            "Ki":   [0x6F, 0x17],   # EF_Ki
            "OPc":  [0x6F, 0x38],   # EF_OPc
            "SPN":  [0x6F, 0x46],   # EF_SPN (Service Provider Name)
        }

        # T-Mobile US MCC/MNC: 310/260 (IMSI must start with 310260)
        required_mccmnc = "310260"

        # --- Automated Key/Cert Loading ---
        # If key/cert files are present, load and inject automatically
        key_files = {
            "Ki": "tmo_ki.hex",         # File with hex string for Ki
            "OPc": "tmo_opc.hex",       # File with hex string for OPc
            "CERT": "tmo_cert.der",     # DER-encoded carrier certificate
            "PRIVKEY": "tmo_privkey.pem" # PEM-encoded private key (for eSIM)
        }
        for k, fname in key_files.items():
            if os.path.exists(fname):
                with open(fname, 'rb') as f:
                    if k in ["Ki", "OPc"]:
                        # Load as hex string
                        hexstr = f.read().decode().strip().replace(' ', '')
                        self.config[k] = ' '.join([hexstr[i:i+2] for i in range(0, len(hexstr), 2)])
                        self.log(f"[Auto] Loaded {k} from {fname}")
                    elif k == "CERT":
                        self.config[k] = f.read().hex()
                        self.log(f"[Auto] Loaded carrier CERT from {fname}")
                    elif k == "PRIVKEY":
                        self.config[k] = f.read().decode()
                        self.log(f"[Auto] Loaded carrier PRIVKEY from {fname}")
        self.save_config()

        # --- Carrier-Specific Personalization ---
        for key, fid in tmo_files.items():
            if key in self.config:
                select_ef = [0x00, 0xA4, 0x02, 0x00, 0x02] + fid
                self.send_apdu(select_ef, f"[T-Mobile MVNO] Select EF_{key}", emulator=emulator)
                try:
                    data_bytes = [int(x, 16) for x in self.config[key].split()]
                except Exception:
                    self.log(f"Invalid hex data for {key} in config. Skipping.")
                    continue
                if key == "IMSI":
                    imsi_str = ''.join(f"{b:02X}" for b in data_bytes)
                    if not imsi_str.startswith(required_mccmnc):
                        self.log(f"[T-Mobile MVNO] IMSI must start with {required_mccmnc}. Provided: {imsi_str}")
                        continue
                if key == "SPN":
                    spn_ascii = self.config[key].encode('ascii')
                    data_bytes = list(spn_ascii[:16]) + [0xFF] * (16 - len(spn_ascii[:16]))
                upd = [0x00, 0xD6, 0x00, 0x00, len(data_bytes)] + data_bytes
                self.send_apdu(upd, f"[T-Mobile MVNO] Update EF_{key} (from config)", emulator=emulator)
            else:
                self.log(f"[T-Mobile MVNO] {key} not set in config. Skipping EF_{key} update.")

        # --- Carrier Certificate Injection (eSIM, optional) ---
        # If CERT and PRIVKEY are present, perform a placeholder secure injection step
        if "CERT" in self.config and "PRIVKEY" in self.config:
            self.log("[T-Mobile MVNO] Injecting carrier certificate and private key (placeholder, automate in production)")
            # Example: send STORE DATA or proprietary APDU for cert/key
            # self.send_apdu(...)

        # --- Android Export Support ---
        if export_android:
            # Export config as JSON and as base64 for QR (Android eSIM import)
            export_json = json.dumps(self.config, indent=2)
            with open(export_android, 'w') as f:
                f.write(export_json)
            self.log(f"[Android Export] Exported config to {export_android}")
            # Optionally, print base64 for QR code
            b64 = base64.b64encode(export_json.encode()).decode()
            self.log(f"[Android Export] Base64 for QR: {b64[:60]}... (truncated)")

        self.log("--- Personalization Session Complete ---")
        print("Personalization complete. See log for details.")

    def set_config(self, key, value):
        # Set a configuration value (IMSI, Ki, OPc, SPN, etc.) for personalization.
        # Use via CLI or Python API.
        self.config[key] = value
        self.save_config()
        print(f"Set config: {key} = {value}")

import argparse


def lint_code():
    # Basic linter for style and clarity (PEP8, unused imports, etc.)
    import subprocess
    print("\n[Lint] Running flake8 for style checks...")
    try:
        result = subprocess.run([sys.executable, '-m', 'flake8', __file__], capture_output=True, text=True)
        if result.returncode == 0:
            print("[Lint] No issues found.")
        else:
            print(result.stdout)
    except Exception as e:
        print(f"[Lint] flake8 not available: {e}")

def main():
    # Main CLI entry point. Parses arguments and dispatches to the correct function.
    # All CLI commands are documented above and in the argparse help.
    parser = argparse.ArgumentParser(description="PCSC SIM/eSIM Issuer Tool - Full Standards Support")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # eSIM/GSMA SGP.02/3GPP TS 31.102
    issue_parser = subparsers.add_parser("esim-issue", help="Issue an eSIM using GSMA SGP.02/3GPP TS 31.102")
    issue_parser.add_argument("--reader", type=int, default=0, help="PCSC reader index (default: 0)")
    issue_parser.add_argument("--emulator", action="store_true", help="Run in emulator mode (no real card required)")
    issue_parser.add_argument("--export-android", type=str, help="Export config for Android eSIM import (filename)")
    issue_parser.add_argument("--frequency", type=str, help="Set radio frequency band/profile (e.g., 900MHz, 2100MHz, b66, n78, b20, b28, n77, n79, ALL). For emergency: b20, b28, n78, n77, etc.")
    issue_parser.add_argument("--mode", type=str, help="Set operational mode (e.g., GSM, UMTS, LTE, 5G, TEST, PRODUCTION)")
    issue_parser.add_argument("--signal-power", type=str, help="Set signal power in dBm (e.g., 23, 20, 10)")
    issue_parser.add_argument("--emergency-profile", action="store_true", help="Enable emergency services profile (e.g., 911/112/PSAP-only)")
    issue_parser.add_argument("--generate-qr", nargs=2, metavar=("SMDP_ADDRESS", "ACTIVATION_CODE"), help="Generate eSIM QR code with SM-DP+ address and activation code")

    # Classic SIM/3GPP TS 51.011/ETSI TS 102 221
    sim_parser = subparsers.add_parser("sim-issue", help="Issue a classic SIM using 3GPP TS 51.011/ETSI TS 102 221")
    sim_parser.add_argument("--reader", type=int, default=0, help="PCSC reader index (default: 0)")
    sim_parser.add_argument("--emulator", action="store_true", help="Run in emulator mode (no real card required)")
    sim_parser.add_argument("--frequency", type=str, help="Set radio frequency band/profile (e.g., 900MHz, 2100MHz, b66, n78, b20, b28, n77, n79, ALL). For emergency: b20, b28, n78, n77, etc.")
    sim_parser.add_argument("--mode", type=str, help="Set operational mode (e.g., GSM, UMTS, LTE, 5G, TEST, PRODUCTION)")
    sim_parser.add_argument("--signal-power", type=str, help="Set signal power in dBm (e.g., 23, 20, 10)")
    sim_parser.add_argument("--emergency-profile", action="store_true", help="Enable emergency services profile (e.g., 911/112/PSAP-only)")

    # Legacy 3G/UMTS/USIM
    umts_parser = subparsers.add_parser("umts-issue", help="Issue a USIM/3G card (legacy/3GPP TS 31.102)")
    umts_parser.add_argument("--reader", type=int, default=0, help="PCSC reader index (default: 0)")
    umts_parser.add_argument("--emulator", action="store_true", help="Run in emulator mode (no real card required)")
    umts_parser.add_argument("--frequency", type=str, help="Set radio frequency band/profile (e.g., 900MHz, 2100MHz, b66, n78, b20, b28, n77, n79, ALL). For emergency: b20, b28, n78, n77, etc.")
    umts_parser.add_argument("--mode", type=str, help="Set operational mode (e.g., GSM, UMTS, LTE, 5G, TEST, PRODUCTION)")
    umts_parser.add_argument("--signal-power", type=str, help="Set signal power in dBm (e.g., 23, 20, 10)")
    umts_parser.add_argument("--emergency-profile", action="store_true", help="Enable emergency services profile (e.g., 911/112/PSAP-only)")

    # set-config command
    config_parser = subparsers.add_parser("set-config", help="Set a configuration value for issuance")
    config_parser.add_argument("key", type=str, help="Configuration key")
    config_parser.add_argument("value", type=str, help="Configuration value")

    # generate-qr command
    qr_parser = subparsers.add_parser("generate-qr", help="Generate eSIM QR code per GSMA SGP.22")
    qr_parser.add_argument("smdp_address", type=str, help="SM-DP+ server address (e.g., sm-dp+.example.com)")
    qr_parser.add_argument("activation_code", type=str, help="Activation code for the eSIM profile")
    qr_parser.add_argument("--output", type=str, default="esim_qr.png", help="Output filename for QR code (default: esim_qr.png)")
    qr_parser.add_argument("--save-to-db", action="store_true", help="Save QR code and profile data to SQLite database")
    qr_parser.add_argument("--profile-id", type=str, help="eSIM profile identifier (required with --save-to-db)")
    qr_parser.add_argument("--iccid", type=str, help="ICCID (required with --save-to-db, or auto-generate if omitted)")
    qr_parser.add_argument("--db", type=str, default="esim_gsma.db", help="Database file path (default: esim_gsma.db)")

    args = parser.parse_args()

    issuer = SimCardIssuer()

    if args.command == "set-config":
        # Set a personalization/config value (IMSI, Ki, OPc, SPN, etc.)
        issuer.set_config(args.key, args.value)
        return

    if args.command == "generate-qr":
        # Generate eSIM QR code per GSMA SGP.22 standard
        try:
            # Validate and prepare parameters for database storage
            save_to_db = args.save_to_db
            profile_id = None
            iccid = None

            if save_to_db:
                if not args.profile_id:
                    print("Error: --profile-id is required when using --save-to-db")
                    sys.exit(1)

                profile_id = args.profile_id

                # Generate ICCID if not provided
                if args.iccid:
                    iccid = args.iccid
                else:
                    iccid = SimCardIssuer.generate_iccid()
                    print(f"[Auto-generated] ICCID: {iccid}")

            lpa_string = SimCardIssuer.generate_esim_qr_code(
                args.smdp_address,
                args.activation_code,
                args.output,
                save_to_db=save_to_db,
                profile_id=profile_id,
                iccid=iccid,
                db_path=args.db
            )
            print(f"\n[QR Code Generated]")
            print(f"File: {args.output}")
            print(f"LPA String: {lpa_string}")
            if save_to_db:
                print(f"Profile ID: {profile_id}")
                print(f"ICCID: {iccid}")
            print(f"\nUsers can scan this QR code to activate the eSIM profile on their device.")
            print(f"Alternatively, they can manually enter: {lpa_string}")
        except ImportError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Failed to generate QR code: {e}")
            sys.exit(1)
        return

    # eSIM/GSMA SGP.02/3GPP TS 31.102
    if args.command == "esim-issue":
        # Issue an eSIM profile. All options are logged and exported. Use --emulator for test/dev.
        # Test: Generate IMSI and IMEI, set in config, and run issuance
        imsi = SimCardIssuer.generate_imsi()
        imei = SimCardIssuer.generate_imei()
        print(f"[Test] Generated IMSI: {imsi}")
        print(f"[Test] Generated IMEI: {imei}")
        issuer.set_config("IMSI", ' '.join([imsi[i:i+2] for i in range(0, len(imsi), 2)]))
        issuer.set_config("IMEI", imei)
        # Set FREQUENCY, MODE, SIGNAL_POWER, and EMERGENCY_PROFILE if provided
        if hasattr(args, "frequency") and args.frequency:
            issuer.set_config("FREQUENCY", args.frequency)
            print(f"[Automation] Frequency set to: {args.frequency} (bands: {args.frequency})")
        if hasattr(args, "mode") and args.mode:
            issuer.set_config("MODE", args.mode)
            print(f"[Automation] Mode set to: {args.mode}")
        if hasattr(args, "signal_power") and args.signal_power:
            issuer.set_config("SIGNAL_POWER", args.signal_power)
            print(f"[Automation] Signal power set to: {args.signal_power} dBm")
        if hasattr(args, "emergency_profile") and args.emergency_profile:
            issuer.set_config("EMERGENCY_PROFILE", True)
            print("[Automation] Emergency services profile enabled. This SIM/eSIM will be marked for emergency use only (911/112/PSAP).")
        # Generate QR code if requested
        if hasattr(args, "generate_qr") and args.generate_qr:
            try:
                smdp_address, activation_code = args.generate_qr
                qr_filename = f"esim_qr_{activation_code[:8]}.png"
                lpa_string = SimCardIssuer.generate_esim_qr_code(smdp_address, activation_code, qr_filename)
                print(f"\n[eSIM QR Code Generated]")
                print(f"File: {qr_filename}")
                print(f"LPA String: {lpa_string}")
            except Exception as e:
                print(f"Warning: Failed to generate QR code: {e}")
        if args.emulator:
            issuer.issuer_mode(emulator=True, export_android=args.export_android)
            lint_code()
            return
        r = issuer.list_readers()
        if not r:
            sys.exit(1)
        idx = args.reader
        if idx >= len(r) or idx < 0:
            print(f"Invalid reader index: {idx}")
            sys.exit(1)
        if not issuer.connect(idx):
            sys.exit(1)
        issuer.issuer_mode(emulator=False, export_android=args.export_android)
        lint_code()

    # Classic SIM/3GPP TS 51.011/ETSI TS 102 221
    if args.command == "sim-issue":
        # Issue a classic SIM profile. All options are logged and exported. Use --emulator for test/dev.
        # Set FREQUENCY, MODE, and SIGNAL_POWER if provided
        if hasattr(args, "frequency") and args.frequency:
            issuer.set_config("FREQUENCY", args.frequency)
        if hasattr(args, "mode") and args.mode:
            issuer.set_config("MODE", args.mode)
        if hasattr(args, "signal_power") and args.signal_power:
            issuer.set_config("SIGNAL_POWER", args.signal_power)
        if args.emulator:
            issuer.sim_apdu_mode(emulator=True)
            lint_code()
            return
        r = issuer.list_readers()
        if not r:
            sys.exit(1)
        idx = args.reader
        if idx >= len(r) or idx < 0:
            print(f"Invalid reader index: {idx}")
            sys.exit(1)
        if not issuer.connect(idx):
            sys.exit(1)
        issuer.sim_apdu_mode(emulator=False)
        lint_code()

    # Legacy 3G/UMTS/USIM
    if args.command == "umts-issue":
        # Issue a USIM/3G profile. All options are logged and exported. Use --emulator for test/dev.
        # Set FREQUENCY, MODE, and SIGNAL_POWER if provided
        if hasattr(args, "frequency") and args.frequency:
            issuer.set_config("FREQUENCY", args.frequency)
        if hasattr(args, "mode") and args.mode:
            issuer.set_config("MODE", args.mode)
        if hasattr(args, "signal_power") and args.signal_power:
            issuer.set_config("SIGNAL_POWER", args.signal_power)
        if args.emulator:
            issuer.umts_apdu_mode(emulator=True)
            lint_code()
            return
        r = issuer.list_readers()
        if not r:
            sys.exit(1)
        idx = args.reader
        if idx >= len(r) or idx < 0:
            print(f"Invalid reader index: {idx}")
            sys.exit(1)
        if not issuer.connect(idx):
            sys.exit(1)
        issuer.umts_apdu_mode(emulator=False)
        lint_code()

if __name__ == "__main__":
    main()
