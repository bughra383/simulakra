#!/usr/bin/env python3
"""
Manual Campaign Completion Script

Use this script to manually complete a running campaign and process results.
Useful for testing when you don't want to wait for the automatic timeout.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from phishbot import PhishingCampaignManager

def main():
    """Main function to manually complete a campaign."""
    if len(sys.argv) != 2:
        print("Usage: python manual_complete.py <campaign_id>")
        print("Example: python manual_complete.py 12")
        sys.exit(1)
    
    try:
        campaign_id = int(sys.argv[1])
    except ValueError:
        print("Error: Campaign ID must be a number")
        sys.exit(1)
    
    print(f"Manual Campaign Completion Tool")
    print(f"Campaign ID: {campaign_id}")
    print("=" * 40)
    
    try:
        manager = PhishingCampaignManager()
        
        # Check if campaign exists
        print(f"Fetching campaign {campaign_id} details...")
        campaign = manager.api.get_campaign(campaign_id)
        campaign_summary = manager.api.get_campaign_summary(campaign_id)
        
        print(f"Campaign Name: {campaign.get('name', 'Unknown')}")
        print(f"Status: {campaign.get('status', 'Unknown')}")
        
        stats = campaign_summary.get('stats', {})
        print(f"Stats: {stats.get('sent', 0)}/{stats.get('total', 0)} sent, "
              f"{stats.get('opened', 0)} opened, {stats.get('clicked', 0)} clicked, "
              f"{stats.get('submitted_data', 0)} submitted")
        
        print("\nProcessing campaign results...")
        
        # Get detailed results with improved extraction
        campaign = manager.api.get_campaign(campaign_id)
        affected_users = manager.extract_campaign_results(campaign)
        
        if affected_users:
            print(f"\nFound {len(affected_users)} affected users:")
            for user in affected_users:
                print(f"  - {user['email']}: {user['event_type']} at {user['event_time']}")
            
            # Save results
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_filename = f"campaign_{campaign_id}_results_{timestamp}.csv"
            
            manager.save_results_csv(affected_users, results_filename)
            print(f"\nResults saved to: {results_filename}")
            
            # Send warning emails if configured
            if manager.config['campaign'].get('send_warning_emails', True):
                print("\nSending warning emails...")
                manager.send_warning_emails(affected_users)
                print("Warning emails sent!")
            else:
                print("\nWarning emails disabled in configuration")
        else:
            print("\nNo affected users found in standard extraction")
            
            # Debug: Show all timeline events to see what we're missing
            summary = manager.api.get_campaign_summary(campaign_id)
            timeline = summary.get('timeline', [])
            print(f"\nDebug: Found {len(timeline)} timeline events:")
            for i, event in enumerate(timeline, 1):
                print(f"  {i}. Message: '{event.get('message', 'Unknown')}' - Email: {event.get('email', 'No email')}")
                if event.get('details'):
                    print(f"      Details: {event.get('details', {})}")
            
            # Check stats vs events
            if stats.get('clicked', 0) > 0 or stats.get('submitted_data', 0) > 0:
                print(f"\n  Mismatch detected!")
                print(f"    Stats show {stats.get('clicked', 0)} clicks and {stats.get('submitted_data', 0)} submissions")
                print(f"    But no matching events found in timeline")
                print(f"    This suggests the event message format is different than expected")
        
        print("\n Campaign processing completed!")
        print("Check the results CSV file and email logs for details.")
        
    except KeyboardInterrupt:
        print("\n  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
