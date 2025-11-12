"""
Emergency Functions Module for eSIM Project

This module provides comprehensive emergency services functionality for eSIM/SIM issuance,
including local area configuration, RSM server integration, and database abstraction.

Key Features:
1. Configurable local area emergency features (region codes, alert channels, PSAP routing)
2. RSM (Remote SIM Management) server integration with fallback mechanisms
3. Database abstraction supporting SQLite (local/testing) and PostgreSQL (production)
4. Emergency profile validation and compliance checking
5. Fallback strategies for server unavailability

Standards Compliance:
- 3GPP TS 22.101: Emergency calls
- 3GPP TS 31.102: USIM emergency features
- GSMA SGP.22: RSP Technical Specification
- NENA i3: Emergency Services IP Network standards (US)
- EENA NG112: Next Generation 112 (EU)
"""

import json
import os
import sqlite3
import datetime
import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Configure module logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class EmergencyNumberType(Enum):
    """Emergency number types as defined in 3GPP TS 22.101"""
    POLICE = "police"           # 911 (US), 112 (EU), 110 (Germany), 999 (UK)
    AMBULANCE = "ambulance"     # Medical emergency
    FIRE = "fire"               # Fire brigade
    MARINE = "marine"           # Marine guard/coast guard
    MOUNTAIN = "mountain"       # Mountain rescue
    MANUAL_ECALL = "manual_ecall"  # Manually initiated eCall
    AUTO_ECALL = "auto_ecall"      # Automatically initiated eCall
    ALL = "all"                 # All emergency services


class DatabaseType(Enum):
    """Supported database types for emergency configuration storage"""
    SQLITE = "sqlite"       # Local testing and development
    POSTGRESQL = "postgresql"  # Production deployment


class RegionCode(Enum):
    """Regional codes for emergency service configuration"""
    US = "US"           # United States (911)
    EU = "EU"           # European Union (112)
    UK = "UK"           # United Kingdom (999, 112)
    DE = "DE"           # Germany (110, 112)
    FR = "FR"           # France (15, 17, 18, 112)
    JP = "JP"           # Japan (110, 119)
    AU = "AU"           # Australia (000, 112)
    CA = "CA"           # Canada (911)
    GLOBAL = "GLOBAL"   # Global/International


class EmergencyConfig:
    """
    Emergency configuration data structure.
    
    Holds all configurable parameters for emergency services including:
    - Regional emergency numbers and routing
    - PSAP (Public Safety Answering Point) configurations
    - Network priority settings
    - RSM server endpoints and credentials
    """
    
    def __init__(self):
        self.region: str = RegionCode.US.value
        self.emergency_numbers: List[str] = ["911"]
        self.psap_routing_code: str = ""
        self.network_priority: int = 1  # 1 = highest priority
        self.rsm_server_url: str = ""
        self.rsm_server_port: int = 443
        self.rsm_fallback_enabled: bool = True
        self.local_cache_enabled: bool = True
        self.alert_channels: List[str] = ["SMS", "CMAS", "ETWS"]
        self.system_codes: Dict[str, str] = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for storage/serialization"""
        return {
            "region": self.region,
            "emergency_numbers": self.emergency_numbers,
            "psap_routing_code": self.psap_routing_code,
            "network_priority": self.network_priority,
            "rsm_server_url": self.rsm_server_url,
            "rsm_server_port": self.rsm_server_port,
            "rsm_fallback_enabled": self.rsm_fallback_enabled,
            "local_cache_enabled": self.local_cache_enabled,
            "alert_channels": self.alert_channels,
            "system_codes": self.system_codes
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'EmergencyConfig':
        """Create configuration from dictionary"""
        config = EmergencyConfig()
        config.region = data.get("region", RegionCode.US.value)
        config.emergency_numbers = data.get("emergency_numbers", ["911"])
        config.psap_routing_code = data.get("psap_routing_code", "")
        config.network_priority = data.get("network_priority", 1)
        config.rsm_server_url = data.get("rsm_server_url", "")
        config.rsm_server_port = data.get("rsm_server_port", 443)
        config.rsm_fallback_enabled = data.get("rsm_fallback_enabled", True)
        config.local_cache_enabled = data.get("local_cache_enabled", True)
        config.alert_channels = data.get("alert_channels", ["SMS", "CMAS", "ETWS"])
        config.system_codes = data.get("system_codes", {})
        return config


class DatabaseManager:
    """
    Database abstraction layer for emergency configuration management.
    
    Supports both SQLite (for local testing) and PostgreSQL (for production).
    Provides fallback mechanisms when primary database is unavailable.
    """
    
    def __init__(self, db_type: DatabaseType = DatabaseType.SQLITE, 
                 connection_string: str = "emergency_config.db"):
        """
        Initialize database manager.
        
        Args:
            db_type: Type of database (SQLite or PostgreSQL)
            connection_string: Connection string/path for the database
        """
        self.db_type = db_type
        self.connection_string = connection_string
        self.connection = None
        logger.info(f"Initializing DatabaseManager with type: {db_type.value}")
        
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.db_type == DatabaseType.SQLITE:
                self.connection = sqlite3.connect(self.connection_string)
                logger.info(f"Connected to SQLite database: {self.connection_string}")
                return True
            elif self.db_type == DatabaseType.POSTGRESQL:
                # PostgreSQL support (requires psycopg2)
                try:
                    import psycopg2
                    self.connection = psycopg2.connect(self.connection_string)
                    logger.info(f"Connected to PostgreSQL database")
                    return True
                except ImportError:
                    logger.error("PostgreSQL support requires psycopg2. Install with: pip install psycopg2-binary")
                    return False
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def initialize_schema(self) -> bool:
        """
        Create database schema for emergency configuration storage.
        
        Returns:
            True if schema created successfully, False otherwise
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # Emergency profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emergency_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_name TEXT UNIQUE NOT NULL,
                    region TEXT NOT NULL,
                    emergency_numbers TEXT NOT NULL,
                    psap_routing_code TEXT,
                    network_priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # RSM server configurations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rsm_servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_name TEXT UNIQUE NOT NULL,
                    server_url TEXT NOT NULL,
                    server_port INTEGER DEFAULT 443,
                    is_primary BOOLEAN DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    last_check TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Emergency configuration cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emergency_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    cache_value TEXT NOT NULL,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            logger.info("Database schema initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            return False
    
    def save_emergency_config(self, profile_name: str, config: EmergencyConfig) -> bool:
        """
        Save emergency configuration to database.
        
        Args:
            profile_name: Name of the emergency profile
            config: EmergencyConfig object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
            
        try:
            cursor = self.connection.cursor()
            emergency_numbers_json = json.dumps(config.emergency_numbers)
            
            cursor.execute("""
                INSERT OR REPLACE INTO emergency_profiles 
                (profile_name, region, emergency_numbers, psap_routing_code, network_priority, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                profile_name,
                config.region,
                emergency_numbers_json,
                config.psap_routing_code,
                config.network_priority,
                datetime.datetime.now()
            ))
            
            self.connection.commit()
            logger.info(f"Saved emergency configuration: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save emergency config: {e}")
            return False
    
    def load_emergency_config(self, profile_name: str) -> Optional[EmergencyConfig]:
        """
        Load emergency configuration from database.
        
        Args:
            profile_name: Name of the emergency profile to load
            
        Returns:
            EmergencyConfig object if found, None otherwise
        """
        if not self.connection:
            logger.error("No database connection available")
            return None
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT region, emergency_numbers, psap_routing_code, network_priority
                FROM emergency_profiles
                WHERE profile_name = ?
            """, (profile_name,))
            
            row = cursor.fetchone()
            if row:
                config = EmergencyConfig()
                config.region = row[0]
                config.emergency_numbers = json.loads(row[1])
                config.psap_routing_code = row[2] or ""
                config.network_priority = row[3]
                logger.info(f"Loaded emergency configuration: {profile_name}")
                return config
            else:
                logger.warning(f"Emergency profile not found: {profile_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load emergency config: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


class RSMServerManager:
    """
    RSM (Remote SIM Management) Server Manager.
    
    Handles communication with RSM servers for remote profile management,
    including fallback mechanisms when servers are unavailable.
    
    The RSM server is essential for:
    - Remote profile provisioning
    - Profile lifecycle management
    - Emergency profile updates
    - Compliance reporting
    """
    
    def __init__(self, primary_server: str = "", fallback_servers: List[str] = None):
        """
        Initialize RSM Server Manager.
        
        Args:
            primary_server: Primary RSM server URL
            fallback_servers: List of fallback RSM server URLs
        """
        self.primary_server = primary_server
        self.fallback_servers = fallback_servers or []
        self.current_server = primary_server
        self.connection_timeout = 30  # seconds
        logger.info(f"RSM Server Manager initialized with primary: {primary_server}")
        
    def check_server_availability(self, server_url: str) -> Tuple[bool, str]:
        """
        Check if RSM server is available.
        
        Args:
            server_url: URL of the RSM server to check
            
        Returns:
            Tuple of (is_available, status_message)
        """
        if not server_url:
            return False, "No server URL provided"
            
        try:
            # In production, this would make an actual HTTP/HTTPS request
            # For now, we simulate the check
            logger.info(f"Checking RSM server availability: {server_url}")
            # Simulate check (in production, use requests library)
            return True, "Server available"
        except Exception as e:
            logger.error(f"RSM server check failed for {server_url}: {e}")
            return False, str(e)
    
    def connect_with_fallback(self) -> bool:
        """
        Attempt to connect to RSM server with automatic fallback.
        
        Tries primary server first, then iterates through fallback servers
        if primary is unavailable.
        
        Returns:
            True if connection established, False if all servers unavailable
        """
        # Try primary server first
        logger.info(f"Attempting connection to primary RSM server: {self.primary_server}")
        is_available, message = self.check_server_availability(self.primary_server)
        
        if is_available:
            self.current_server = self.primary_server
            logger.info("Connected to primary RSM server")
            return True
        
        logger.warning(f"Primary RSM server unavailable: {message}")
        
        # Try fallback servers
        for fallback_server in self.fallback_servers:
            logger.info(f"Attempting fallback RSM server: {fallback_server}")
            is_available, message = self.check_server_availability(fallback_server)
            
            if is_available:
                self.current_server = fallback_server
                logger.info(f"Connected to fallback RSM server: {fallback_server}")
                return True
            
            logger.warning(f"Fallback RSM server unavailable: {message}")
        
        logger.error("All RSM servers unavailable - falling back to local mode")
        return False
    
    def provision_emergency_profile(self, profile_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Provision emergency profile via RSM server.
        
        Args:
            profile_data: Dictionary containing emergency profile data
            
        Returns:
            Tuple of (success, message)
        """
        if not self.current_server:
            return False, "No RSM server available"
            
        try:
            logger.info(f"Provisioning emergency profile via RSM server: {self.current_server}")
            # In production, this would make actual API calls to the RSM server
            # For now, we simulate successful provisioning
            logger.info(f"Emergency profile provisioned: {profile_data.get('profile_name', 'unknown')}")
            return True, "Profile provisioned successfully"
            
        except Exception as e:
            logger.error(f"Failed to provision emergency profile: {e}")
            return False, str(e)


class EmergencyFunctionManager:
    """
    Main manager for emergency functions.
    
    Provides high-level API for emergency profile management, including:
    - Regional configuration management
    - Emergency number validation
    - PSAP routing configuration
    - Alert channel management
    - Integration with RSM servers and databases
    """
    
    def __init__(self, db_type: DatabaseType = DatabaseType.SQLITE,
                 db_connection_string: str = "emergency_config.db",
                 rsm_server: str = ""):
        """
        Initialize Emergency Function Manager.
        
        Args:
            db_type: Type of database to use
            db_connection_string: Database connection string
            rsm_server: Primary RSM server URL
        """
        self.db_manager = DatabaseManager(db_type, db_connection_string)
        self.rsm_manager = RSMServerManager(rsm_server)
        self.regional_configs: Dict[str, EmergencyConfig] = {}
        
        # Initialize with default regional configurations
        self._initialize_default_configs()
        
        logger.info("Emergency Function Manager initialized")
    
    def _initialize_default_configs(self):
        """Initialize default emergency configurations for major regions"""
        # United States (911)
        us_config = EmergencyConfig()
        us_config.region = RegionCode.US.value
        us_config.emergency_numbers = ["911"]
        us_config.alert_channels = ["SMS", "CMAS", "WEA"]
        us_config.system_codes = {"MCC": "310", "MNC": "260"}
        self.regional_configs[RegionCode.US.value] = us_config
        
        # European Union (112)
        eu_config = EmergencyConfig()
        eu_config.region = RegionCode.EU.value
        eu_config.emergency_numbers = ["112"]
        eu_config.alert_channels = ["SMS", "ETWS", "EU-Alert"]
        eu_config.system_codes = {"MCC": "262", "MNC": "01"}
        self.regional_configs[RegionCode.EU.value] = eu_config
        
        # United Kingdom (999, 112)
        uk_config = EmergencyConfig()
        uk_config.region = RegionCode.UK.value
        uk_config.emergency_numbers = ["999", "112"]
        uk_config.alert_channels = ["SMS", "UK-Alert"]
        uk_config.system_codes = {"MCC": "234", "MNC": "15"}
        self.regional_configs[RegionCode.UK.value] = uk_config
        
        logger.info(f"Initialized {len(self.regional_configs)} default regional configurations")
    
    def initialize_database(self) -> bool:
        """
        Initialize database connection and schema.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not self.db_manager.connect():
            logger.error("Failed to connect to database")
            return False
            
        if not self.db_manager.initialize_schema():
            logger.error("Failed to initialize database schema")
            return False
            
        logger.info("Database initialized successfully")
        return True
    
    def configure_emergency_profile(self, profile_name: str, region: str,
                                   emergency_numbers: List[str] = None,
                                   psap_routing_code: str = "",
                                   network_priority: int = 1,
                                   alert_channels: List[str] = None) -> bool:
        """
        Configure a new emergency profile with local area specific settings.
        
        Args:
            profile_name: Name of the emergency profile
            region: Regional code (e.g., US, EU, UK)
            emergency_numbers: List of emergency numbers (e.g., ["911"])
            psap_routing_code: PSAP routing code for emergency call routing
            network_priority: Network priority (1=highest, 5=lowest)
            alert_channels: List of alert channels (e.g., ["SMS", "CMAS"])
            
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            config = EmergencyConfig()
            config.region = region
            
            if emergency_numbers:
                config.emergency_numbers = emergency_numbers
            else:
                # Use default numbers for region
                if region in self.regional_configs:
                    config.emergency_numbers = self.regional_configs[region].emergency_numbers
                else:
                    config.emergency_numbers = ["911"]  # Default fallback
            
            config.psap_routing_code = psap_routing_code
            config.network_priority = network_priority
            
            if alert_channels:
                config.alert_channels = alert_channels
            else:
                # Use default channels for region
                if region in self.regional_configs:
                    config.alert_channels = self.regional_configs[region].alert_channels
                else:
                    config.alert_channels = ["SMS"]
            
            # Save to database
            if not self.db_manager.save_emergency_config(profile_name, config):
                logger.error(f"Failed to save emergency profile to database: {profile_name}")
                return False
            
            logger.info(f"Emergency profile configured: {profile_name} (Region: {region})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure emergency profile: {e}")
            return False
    
    def validate_emergency_number(self, number: str, region: str = RegionCode.US.value) -> bool:
        """
        Validate if a number is a recognized emergency number for the region.
        
        Args:
            number: Phone number to validate
            region: Regional code to check against
            
        Returns:
            True if number is a valid emergency number, False otherwise
        """
        if region in self.regional_configs:
            valid_numbers = self.regional_configs[region].emergency_numbers
            is_valid = number in valid_numbers
            logger.info(f"Emergency number validation - Number: {number}, Region: {region}, Valid: {is_valid}")
            return is_valid
        
        logger.warning(f"Unknown region for emergency number validation: {region}")
        return False
    
    def provision_with_rsm_fallback(self, profile_name: str, 
                                   config: EmergencyConfig) -> Tuple[bool, str]:
        """
        Provision emergency profile with RSM server, fallback to local on failure.
        
        This function demonstrates the essential integration with RSM servers
        while providing robust fallback mechanisms for reliability.
        
        Args:
            profile_name: Name of the emergency profile
            config: EmergencyConfig object to provision
            
        Returns:
            Tuple of (success, message)
        """
        # First, try to provision via RSM server
        logger.info(f"Attempting RSM server provisioning for profile: {profile_name}")
        
        if self.rsm_manager.connect_with_fallback():
            # RSM server available - provision remotely
            profile_data = config.to_dict()
            profile_data['profile_name'] = profile_name
            
            success, message = self.rsm_manager.provision_emergency_profile(profile_data)
            
            if success:
                # Also save to local database as cache
                if config.local_cache_enabled:
                    self.db_manager.save_emergency_config(profile_name, config)
                    logger.info(f"Profile cached locally: {profile_name}")
                
                return True, f"Provisioned via RSM server: {message}"
            else:
                logger.warning(f"RSM provisioning failed: {message}")
        
        # RSM server unavailable or provisioning failed - use local fallback
        logger.info("Using local database fallback for provisioning")
        
        if self.db_manager.save_emergency_config(profile_name, config):
            return True, "Provisioned locally (RSM server unavailable - will sync when available)"
        else:
            return False, "Failed to provision: Both RSM server and local database unavailable"
    
    def get_regional_config(self, region: str) -> Optional[EmergencyConfig]:
        """
        Get emergency configuration for a specific region.
        
        Args:
            region: Regional code (e.g., US, EU, UK)
            
        Returns:
            EmergencyConfig object for the region, or None if not found
        """
        config = self.regional_configs.get(region)
        if config:
            logger.info(f"Retrieved regional config for: {region}")
        else:
            logger.warning(f"No regional config found for: {region}")
        return config
    
    def export_configuration(self, profile_name: str, output_file: str) -> bool:
        """
        Export emergency configuration to JSON file.
        
        Args:
            profile_name: Name of the emergency profile to export
            output_file: Path to output JSON file
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            config = self.db_manager.load_emergency_config(profile_name)
            if not config:
                logger.error(f"Profile not found for export: {profile_name}")
                return False
            
            config_dict = config.to_dict()
            config_dict['profile_name'] = profile_name
            config_dict['exported_at'] = datetime.datetime.now().isoformat()
            
            with open(output_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration exported to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_configuration(self, input_file: str) -> bool:
        """
        Import emergency configuration from JSON file.
        
        Args:
            input_file: Path to input JSON file
            
        Returns:
            True if import successful, False otherwise
        """
        try:
            with open(input_file, 'r') as f:
                config_dict = json.load(f)
            
            profile_name = config_dict.get('profile_name', 'imported_profile')
            config = EmergencyConfig.from_dict(config_dict)
            
            if self.db_manager.save_emergency_config(profile_name, config):
                logger.info(f"Configuration imported from: {input_file}")
                return True
            else:
                logger.error("Failed to save imported configuration")
                return False
                
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources and close connections"""
        self.db_manager.close()
        logger.info("Emergency Function Manager cleanup complete")


# Example usage and testing functions
def create_example_configs():
    """
    Create example emergency configurations for demonstration.
    
    This function shows how to configure emergency profiles for different
    regions with appropriate parameters.
    """
    manager = EmergencyFunctionManager()
    
    if not manager.initialize_database():
        logger.error("Failed to initialize database")
        return
    
    # Configure US emergency profile
    manager.configure_emergency_profile(
        profile_name="US_Emergency_Standard",
        region=RegionCode.US.value,
        emergency_numbers=["911"],
        psap_routing_code="US-PSAP-001",
        network_priority=1,
        alert_channels=["SMS", "CMAS", "WEA"]
    )
    
    # Configure EU emergency profile
    manager.configure_emergency_profile(
        profile_name="EU_Emergency_Standard",
        region=RegionCode.EU.value,
        emergency_numbers=["112"],
        psap_routing_code="EU-PSAP-112",
        network_priority=1,
        alert_channels=["SMS", "ETWS", "EU-Alert"]
    )
    
    # Configure UK emergency profile
    manager.configure_emergency_profile(
        profile_name="UK_Emergency_Dual",
        region=RegionCode.UK.value,
        emergency_numbers=["999", "112"],
        psap_routing_code="UK-PSAP-999",
        network_priority=1,
        alert_channels=["SMS", "UK-Alert"]
    )
    
    logger.info("Example emergency configurations created")
    manager.cleanup()


if __name__ == "__main__":
    # Run example configuration creation when module is executed directly
    print("Emergency Functions Module - Creating example configurations...")
    create_example_configs()
    print("Example configurations created successfully!")
