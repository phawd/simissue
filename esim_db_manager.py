#!/usr/bin/env python3
"""
eSIM Database Manager Script

This script provides utilities for managing the eSIM database including:
- Creating/migrating database schema
- Inserting eSIM data (profile ID, ICCID, QR code)
- Retrieving profile information
- Rendering QR codes as image files

Usage:
    python esim_db_manager.py init                    # Initialize database
    python esim_db_manager.py insert <profile_id> <iccid> [--qr-file <path>]
    python esim_db_manager.py retrieve <iccid>        # Retrieve by ICCID
    python esim_db_manager.py list [--limit N]        # List all profiles
    python esim_db_manager.py export-qr <record_id> <output_file>
"""

import argparse
import sys
import os
from typing import Optional
from database import DatabaseConnection, GSMAComplianceDB


def init_database(db_path: str = "esim_gsma.db"):
    """
    Initialize the database and create schema.

    Args:
        db_path: Path to SQLite database file
    """
    print(f"Initializing database: {db_path}")

    with DatabaseConnection(db_path) as db_conn:
        gsma_db = GSMAComplianceDB(db_conn)
        gsma_db.create_schema()

    print("Database initialized successfully")
    print("Schema created with 'gsma_compliance' table")


def insert_esim_data(db_path: str, profile_id: str, iccid: str,
                     qr_file: Optional[str] = None):
    """
    Insert eSIM data into the database.

    Args:
        db_path: Path to SQLite database file
        profile_id: eSIM profile identifier
        iccid: Integrated Circuit Card Identifier
        qr_file: Path to QR code image file (optional)
    """
    print("Inserting eSIM data:")
    print(f"  Profile ID: {profile_id}")
    print(f"  ICCID: {iccid}")

    # Load QR code if provided
    qr_code_data = None
    if qr_file:
        if not os.path.exists(qr_file):
            print(f"Error: QR code file not found: {qr_file}")
            sys.exit(1)

        with open(qr_file, 'rb') as f:
            qr_code_data = f.read()
        print(f"  QR Code: {qr_file} ({len(qr_code_data)} bytes)")

    # Insert into database
    with DatabaseConnection(db_path) as db_conn:
        gsma_db = GSMAComplianceDB(db_conn)

        try:
            record_id = gsma_db.insert_esim_data(profile_id, iccid, qr_code_data)
            print("\neSIM data inserted successfully")
            print(f"Record ID: {record_id}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


def retrieve_profile(db_path: str, iccid: str):
    """
    Retrieve and display profile information by ICCID.

    Args:
        db_path: Path to SQLite database file
        iccid: Integrated Circuit Card Identifier
    """
    with DatabaseConnection(db_path) as db_conn:
        gsma_db = GSMAComplianceDB(db_conn)

        profile = gsma_db.get_profile_by_iccid(iccid)

        if profile:
            print("\nProfile found:")
            print(f"  Record ID: {profile['id']}")
            print(f"  Profile ID: {profile['profile_id']}")
            print(f"  ICCID: {profile['iccid']}")
            print(f"  Timestamp: {profile['timestamp']}")

            if profile['qr_code']:
                print(f"  QR Code: Stored ({len(profile['qr_code'])} bytes)")
            else:
                print("  QR Code: Not stored")
        else:
            print(f"No profile found with ICCID: {iccid}")


def list_profiles(db_path: str, limit: int = 100):
    """
    List all profiles in the database.

    Args:
        db_path: Path to SQLite database file
        limit: Maximum number of records to display
    """
    with DatabaseConnection(db_path) as db_conn:
        gsma_db = GSMAComplianceDB(db_conn)

        profiles = gsma_db.get_all_profiles(limit=limit)

        if profiles:
            print(f"\nFound {len(profiles)} profile(s):\n")

            for profile in profiles:
                print(f"Record ID: {profile['id']}")
                print(f"  Profile ID: {profile['profile_id']}")
                print(f"  ICCID: {profile['iccid']}")
                print(f"  Timestamp: {profile['timestamp']}")

                if profile['qr_code']:
                    print(f"  QR Code: Stored ({len(profile['qr_code'])} bytes)")
                else:
                    print("  QR Code: Not stored")
                print()
        else:
            print("No profiles found in database")


def export_qr_code(db_path: str, record_id: int, output_file: str):
    """
    Export QR code from database to an image file.

    Args:
        db_path: Path to SQLite database file
        record_id: Database record ID
        output_file: Path where QR code should be saved
    """
    print(f"Exporting QR code for record ID: {record_id}")

    with DatabaseConnection(db_path) as db_conn:
        gsma_db = GSMAComplianceDB(db_conn)

        success = gsma_db.save_qr_code_to_file(record_id, output_file)

        if success:
            print(f"QR code exported successfully to: {output_file}")
        else:
            print("Failed to export QR code")
            sys.exit(1)


def validate_essential_variables(profile_id: str, iccid: str) -> bool:
    """
    Validate that essential eSIM variables are properly formatted.

    Args:
        profile_id: eSIM profile identifier
        iccid: Integrated Circuit Card Identifier

    Returns:
        True if all variables are valid, False otherwise
    """
    errors = []

    # Validate Profile ID
    if not profile_id or len(profile_id.strip()) == 0:
        errors.append("Profile ID cannot be empty")

    # Validate ICCID (should be 19-20 digits)
    if not iccid or len(iccid.strip()) == 0:
        errors.append("ICCID cannot be empty")
    elif not iccid.isdigit():
        errors.append("ICCID must contain only digits")
    elif len(iccid) < 19 or len(iccid) > 20:
        errors.append(f"ICCID must be 19-20 digits (got {len(iccid)})")

    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def main():
    """Main entry point for the eSIM database manager."""
    parser = argparse.ArgumentParser(
        description="eSIM Database Manager - Manage eSIM profiles with SQLite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python esim_db_manager.py init

  # Insert eSIM data without QR code
  python esim_db_manager.py insert PROF-001 89012345678901234567

  # Insert eSIM data with QR code
  python esim_db_manager.py insert PROF-001 89012345678901234567 --qr-file esim_qr.png

  # Retrieve profile by ICCID
  python esim_db_manager.py retrieve 89012345678901234567

  # List all profiles
  python esim_db_manager.py list

  # Export QR code
  python esim_db_manager.py export-qr 1 output_qr.png
        """
    )

    parser.add_argument(
        '--db',
        default='esim_gsma.db',
        help='Database file path (default: esim_gsma.db)'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Init command
    subparsers.add_parser('init', help='Initialize database and create schema')

    # Insert command
    insert_parser = subparsers.add_parser('insert', help='Insert eSIM data')
    insert_parser.add_argument('profile_id', help='eSIM profile identifier')
    insert_parser.add_argument('iccid', help='Integrated Circuit Card Identifier (19-20 digits)')
    insert_parser.add_argument('--qr-file', help='Path to QR code image file')

    # Retrieve command
    retrieve_parser = subparsers.add_parser('retrieve', help='Retrieve profile by ICCID')
    retrieve_parser.add_argument('iccid', help='Integrated Circuit Card Identifier')

    # List command
    list_parser = subparsers.add_parser('list', help='List all profiles')
    list_parser.add_argument('--limit', type=int, default=100,
                             help='Maximum number of records to display')

    # Export QR command
    export_parser = subparsers.add_parser('export-qr', help='Export QR code to file')
    export_parser.add_argument('record_id', type=int, help='Database record ID')
    export_parser.add_argument('output_file', help='Output file path for QR code')

    args = parser.parse_args()

    # Execute command
    if args.command == 'init':
        init_database(args.db)

    elif args.command == 'insert':
        # Validate essential variables
        if not validate_essential_variables(args.profile_id, args.iccid):
            sys.exit(1)

        insert_esim_data(args.db, args.profile_id, args.iccid, args.qr_file)

    elif args.command == 'retrieve':
        retrieve_profile(args.db, args.iccid)

    elif args.command == 'list':
        list_profiles(args.db, args.limit)

    elif args.command == 'export-qr':
        export_qr_code(args.db, args.record_id, args.output_file)


if __name__ == '__main__':
    main()
