"""
Database layer for eSIM issuance with SQLite support.

This module provides a low-coupling database abstraction layer that can be
easily ported to other relational databases. It implements the GSMA compliance
data storage requirements for eSIM profile management.
"""

import sqlite3
from typing import Optional, List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Database connection manager with support for SQLite.

    This class provides a clean abstraction layer for database operations,
    making it easy to migrate to other databases (PostgreSQL, MySQL, etc.)
    in the future by implementing a similar interface.
    """

    def __init__(self, db_path: str = "esim_gsma.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (default: esim_gsma.db)
        """
        self.db_path = db_path
        self.connection = None

    def connect(self) -> sqlite3.Connection:
        """
        Establish connection to the database.

        Returns:
            Database connection object
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
            return self.connection
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class GSMAComplianceDB:
    """
    GSMA compliance database operations for eSIM profile management.

    This class handles all database operations for storing and retrieving
    eSIM profile data including profile IDs, ICCIDs, and QR codes in
    compliance with GSMA SGP.22 standards.
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize GSMA compliance database handler.

        Args:
            db_connection: Database connection object
        """
        self.db_conn = db_connection

    def create_schema(self):
        """
        Create the gsma_compliance table schema.

        Table structure:
        - id: Primary Key (Auto-increment)
        - profile_id: Text field for eSIM profile identifier
        - iccid: Text field for Integrated Circuit Card Identifier
        - qr_code: BLOB field for storing QR code images
        - timestamp: DateTime field with default as current timestamp
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS gsma_compliance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            iccid TEXT NOT NULL UNIQUE,
            qr_code BLOB,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Create index for faster lookups on profile_id
        # Note: ICCID already has an implicit index due to UNIQUE constraint
        create_index_profile_id_sql = """
        CREATE INDEX IF NOT EXISTS idx_profile_id ON gsma_compliance(profile_id);
        """

        try:
            cursor = self.db_conn.connection.cursor()
            cursor.execute(create_table_sql)
            cursor.execute(create_index_profile_id_sql)
            self.db_conn.connection.commit()
            logger.info("Database schema created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating schema: {e}")
            raise

    def insert_esim_data(self, profile_id: str, iccid: str,
                         qr_code: Optional[bytes] = None) -> int:
        """
        Insert eSIM data into the database.

        Args:
            profile_id: eSIM profile identifier
            iccid: Integrated Circuit Card Identifier
            qr_code: QR code image as bytes (optional)

        Returns:
            ID of the inserted record

        Raises:
            sqlite3.IntegrityError: If ICCID already exists
        """
        insert_sql = """
        INSERT INTO gsma_compliance (profile_id, iccid, qr_code)
        VALUES (?, ?, ?);
        """

        try:
            cursor = self.db_conn.connection.cursor()
            cursor.execute(insert_sql, (profile_id, iccid, qr_code))
            self.db_conn.connection.commit()
            record_id = cursor.lastrowid
            logger.info(f"Inserted eSIM data: ID={record_id}, Profile={profile_id}, ICCID={iccid}")
            return record_id
        except sqlite3.IntegrityError:
            logger.error(f"ICCID already exists: {iccid}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Error inserting eSIM data: {e}")
            raise

    def get_profile_by_id(self, record_id: int) -> Optional[Dict]:
        """
        Retrieve eSIM profile data by record ID.

        Args:
            record_id: Database record ID

        Returns:
            Dictionary containing profile data or None if not found
        """
        select_sql = """
        SELECT id, profile_id, iccid, qr_code, timestamp
        FROM gsma_compliance
        WHERE id = ?;
        """

        try:
            cursor = self.db_conn.connection.cursor()
            cursor.execute(select_sql, (record_id,))
            row = cursor.fetchone()

            if row:
                return {
                    'id': row['id'],
                    'profile_id': row['profile_id'],
                    'iccid': row['iccid'],
                    'qr_code': row['qr_code'],
                    'timestamp': row['timestamp']
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving profile by ID: {e}")
            raise

    def get_profile_by_iccid(self, iccid: str) -> Optional[Dict]:
        """
        Retrieve eSIM profile data by ICCID.

        Args:
            iccid: Integrated Circuit Card Identifier

        Returns:
            Dictionary containing profile data or None if not found
        """
        select_sql = """
        SELECT id, profile_id, iccid, qr_code, timestamp
        FROM gsma_compliance
        WHERE iccid = ?;
        """

        try:
            cursor = self.db_conn.connection.cursor()
            cursor.execute(select_sql, (iccid,))
            row = cursor.fetchone()

            if row:
                return {
                    'id': row['id'],
                    'profile_id': row['profile_id'],
                    'iccid': row['iccid'],
                    'qr_code': row['qr_code'],
                    'timestamp': row['timestamp']
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving profile by ICCID: {e}")
            raise

    def get_all_profiles(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Retrieve all eSIM profiles with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of dictionaries containing profile data
        """
        select_sql = """
        SELECT id, profile_id, iccid, qr_code, timestamp
        FROM gsma_compliance
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?;
        """

        try:
            cursor = self.db_conn.connection.cursor()
            cursor.execute(select_sql, (limit, offset))
            rows = cursor.fetchall()

            return [
                {
                    'id': row['id'],
                    'profile_id': row['profile_id'],
                    'iccid': row['iccid'],
                    'qr_code': row['qr_code'],
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all profiles: {e}")
            raise

    def update_qr_code(self, record_id: int, qr_code: bytes) -> bool:
        """
        Update QR code for an existing profile.

        Args:
            record_id: Database record ID
            qr_code: QR code image as bytes

        Returns:
            True if update successful, False otherwise
        """
        update_sql = """
        UPDATE gsma_compliance
        SET qr_code = ?
        WHERE id = ?;
        """

        try:
            cursor = self.db_conn.connection.cursor()
            cursor.execute(update_sql, (qr_code, record_id))
            self.db_conn.connection.commit()

            if cursor.rowcount > 0:
                logger.info(f"Updated QR code for record ID: {record_id}")
                return True
            else:
                logger.warning(f"No record found with ID: {record_id}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error updating QR code: {e}")
            raise

    def delete_profile(self, record_id: int) -> bool:
        """
        Delete an eSIM profile from the database.

        Args:
            record_id: Database record ID

        Returns:
            True if deletion successful, False otherwise
        """
        delete_sql = """
        DELETE FROM gsma_compliance
        WHERE id = ?;
        """

        try:
            cursor = self.db_conn.connection.cursor()
            cursor.execute(delete_sql, (record_id,))
            self.db_conn.connection.commit()

            if cursor.rowcount > 0:
                logger.info(f"Deleted profile with ID: {record_id}")
                return True
            else:
                logger.warning(f"No record found with ID: {record_id}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting profile: {e}")
            raise

    def save_qr_code_to_file(self, record_id: int, output_path: str) -> bool:
        """
        Retrieve QR code from database and save it to a file.

        Args:
            record_id: Database record ID
            output_path: Path where QR code image should be saved

        Returns:
            True if successful, False otherwise
        """
        try:
            profile = self.get_profile_by_id(record_id)

            if not profile:
                logger.error(f"No profile found with ID: {record_id}")
                return False

            if not profile['qr_code']:
                logger.error(f"No QR code stored for profile ID: {record_id}")
                return False

            with open(output_path, 'wb') as f:
                f.write(profile['qr_code'])

            logger.info(f"QR code saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving QR code to file: {e}")
            raise
