#!/usr/bin/env python3
"""
Test script to verify GoPhish API connection and configuration.

This script tests the basic functionality without running a full campaign.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

try:
    from simulakra import PhishingCampaignManager
    print("Successfully imported PhishingCampaignManager")
except ImportError as e:
    print(f"Failed to import PhishingCampaignManager: {e}")
    sys.exit(1)

def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        manager = PhishingCampaignManager()
        print("Configuration loaded successfully")
        return manager
    except SystemExit:
        print("Configuration test failed (this is expected without proper setup)")
        return None
    except Exception as e:
        print(f"Unexpected error in configuration: {e}")
        return None

def test_csv_reading(manager):
    """Test CSV file reading."""
    if not manager:
        return
    
    print("\nTesting CSV reading...")
    try:
        targets = manager.read_targets_csv("targets.csv")
        print(f"Successfully read {len(targets)} targets from CSV")
        
        # Show first target as example
        if targets:
            first_target = targets[0]
            print(f"   Example target: {first_target['first_name']} {first_target['last_name']} ({first_target['email']})")
    except SystemExit:
        print("CSV reading failed")
    except Exception as e:
        print(f"Unexpected error reading CSV: {e}")

def test_environment_variables():
    """Test environment variable loading."""
    print("\nTesting environment variables...")
    
    required_vars = [
        'GOPHISH_API_KEY',
        'MAILGUN_SMTP_SERVER',
        'MAILGUN_SMTP_PORT',
        'MAILGUN_SMTP_USER',
        'MAILGUN_SMTP_PASS'
    ]
    
    placeholder_indicators = [
        'your_',
        'placeholder',
        'example',
        'changeme',
        'replace',
        'here'
    ]
    
    missing_vars = []
    placeholder_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"    {var}: Not set")
            missing_vars.append(var)
        elif any(indicator in value.lower() for indicator in placeholder_indicators):
            print(f"     {var}: Contains placeholder value")
            placeholder_vars.append(var)
        else:
            # Don't print the actual value for security
            print(f"    {var}: {'*' * min(len(value), 10)}")
    
    if missing_vars:
        print(f"\n Missing environment variables: {', '.join(missing_vars)}")
    
    if placeholder_vars:
        print(f"\n Variables with placeholder values: {', '.join(placeholder_vars)}")
        print("   Please update your .env file with actual credentials")
    
    if not missing_vars and not placeholder_vars:
        print("\n All required environment variables are properly set")

def test_file_existence():
    """Test if required files exist."""
    print("\n Testing file existence...")
    
    required_files = [
        'config.yaml',
        'targets.csv',
        '.env.example'
    ]
    
    for filename in required_files:
        if Path(filename).exists():
            print(f"    {filename}: Exists")
        else:
            print(f"    {filename}: Missing")

def main():
    """Run all tests."""
    print(" GoPhish Automation Test Suite")
    print("=" * 40)
    
    # Test file existence first
    test_file_existence()
    
    # Test environment variables
    test_environment_variables()
    
    # Test configuration and CSV
    manager = test_configuration()
    test_csv_reading(manager)
    
    print("\n" + "=" * 40)
    print(" Test completed!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and fill in your credentials")
    print("2. Update config.yaml with your GoPhish server details")
    print("3. Update targets.csv with your actual target list")
    print("4. Run: python simulakra.py")

if __name__ == "__main__":
    main()
