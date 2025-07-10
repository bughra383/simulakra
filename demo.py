#!/usr/bin/env python3
"""
Demo script showing how to use the PhishingCampaignManager for testing
and validation without running an actual campaign.

This script demonstrates the basic functionality and can be used to:
- Test API connectivity
- Validate configuration
- Check that GoPhish objects exist
- Verify CSV file format
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from simulakra import PhishingCampaignManager

def main():
    """Run demo without executing actual campaign."""
    print("GoPhish Campaign Manager Demo")
    print("=" * 50)
    
    # Test 1: Initialize manager
    print("\nTesting initialization...")
    try:
        # This will test config loading and API connection
        manager = PhishingCampaignManager()
        print("Manager initialized successfully")
    except SystemExit as e:
        print(f"Initialization failed with exit code {e.code}")
        print("Check your .env file and config.yaml settings")
        return
    except Exception as e:
        print(f"Unexpected error: {e}")
        return
    
    # Test 2: Read CSV targets
    print("\nTesting CSV reading...")
    try:
        targets = manager.read_targets_csv(manager.config['campaign']['targets_csv'])
        print(f"Successfully read {len(targets)} targets")
        if targets:
            print(f"   Sample target: {targets[0]['first_name']} {targets[0]['last_name']} ({targets[0]['email']})")
    except SystemExit:
        print("CSV reading failed")
        return
    except Exception as e:
        print(f"Unexpected error reading CSV: {e}")
        return
    
    # Test 3: Check GoPhish objects exist
    print("\nTesting GoPhish object availability...")
    
    try:
        # Check SMTP profile
        smtp_name = manager.config['campaign']['smtp_profile']
        smtp_profile = manager.get_smtp_profile(smtp_name)
        print(f"SMTP profile '{smtp_name}' found (ID: {smtp_profile.get('id')})")
    except SystemExit:
        print(f"SMTP profile '{smtp_name}' not found")
        return
    except Exception as e:
        print(f"Error checking SMTP profile: {e}")
        return
    
    try:
        # Check template
        template_name = manager.config['campaign']['template']
        template = manager.get_template(template_name)
        print(f"Template '{template_name}' found (ID: {template.get('id')})")
    except SystemExit:
        print(f"Template '{template_name}' not found")
        return
    except Exception as e:
        print(f"Error checking template: {e}")
        return
    
    try:
        # Check landing page
        page_name = manager.config['campaign']['landing_page']
        landing_page = manager.get_landing_page(page_name)
        print(f"Landing page '{page_name}' found (ID: {landing_page.get('id')})")
    except SystemExit:
        print(f"Landing page '{page_name}' not found")
        return
    except Exception as e:
        print(f"Error checking landing page: {e}")
        return
    
    # Test 4: SMTP credentials check
    print("\n4️⃣ Testing SMTP credentials...")
    required_smtp_vars = [
        'MAILGUN_SMTP_SERVER',
        'MAILGUN_SMTP_PORT', 
        'MAILGUN_SMTP_USER',
        'MAILGUN_SMTP_PASS'
    ]
    
    smtp_ok = True
    for var in required_smtp_vars:
        value = os.getenv(var)
        if value:
            print(f"   {var}: Set")
        else:
            print(f"   {var}: Not set")
            smtp_ok = False
    
    if smtp_ok:
        print(" All SMTP credentials are configured")
    else:
        print(" Some SMTP credentials are missing")
    
    # Summary
    print("\n" + "=" * 50)
    print(" Demo completed successfully!")
    print("\n Summary:")
    print("   API connection working")
    print("   Configuration valid")
    print("   CSV file readable")
    print("   GoPhish objects available")
    
    if smtp_ok:
        print("   SMTP credentials configured")
    else:
        print("   SMTP credentials need attention")
    
    print("\nReady to run actual campaigns!")
    print("\nTo run a real campaign:")
    print("   python simulakra.py")
    

if __name__ == "__main__":
    main()
