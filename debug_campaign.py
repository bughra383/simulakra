#!/usr/bin/env python3
"""
Debug script to check campaign results and timeline data
"""

import json
import sys
from simulakra import PhishingCampaignManager

def debug_campaign_results(campaign_id: int):
    """Debug campaign results by examining raw API responses."""
    try:
        manager = PhishingCampaignManager()
        
        print(f"Debugging campaign {campaign_id} results...")
        print("=" * 50)
        
        # Get campaign details
        campaign = manager.api.get_campaign(campaign_id)
        print(f"Campaign Status: {campaign.get('status', 'Unknown')}")
        print(f"Campaign Name: {campaign.get('name', 'Unknown')}")
        
        # Get campaign summary with detailed output
        summary = manager.api.get_campaign_summary(campaign_id)
        
        print("\nCampaign Stats:")
        stats = summary.get('stats', {})
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nTimeline Events:")
        timeline = summary.get('timeline', [])
        print(f"Total timeline events: {len(timeline)}")
        
        if timeline:
            print("\nAll timeline events:")
            for i, event in enumerate(timeline):
                print(f"\nEvent {i+1}:")
                print(f"  Time: {event.get('time', 'Unknown')}")
                print(f"  Message: {event.get('message', 'Unknown')}")
                print(f"  Email: {event.get('email', 'Unknown')}")
                print(f"  Details: {json.dumps(event.get('details', {}), indent=4)}")
                print(f"  Raw event: {json.dumps(event, indent=4)}")
        else:
            print("  No timeline events found")
        
        print("\nLooking for clicks/submissions...")
        affected_users = []
        
        for event in timeline:
            message = event.get('message', '')
            print(f"  Checking event: '{message}'")
            
            # Check for various possible event types
            if any(keyword in message.lower() for keyword in ['click', 'submit', 'data', 'link']):
                print(f"    Found potential affected user event: {message}")
                details = event.get('details', {})
                email = event.get('email', details.get('email', ''))
                
                affected_users.append({
                    'first_name': details.get('first_name', ''),
                    'last_name': details.get('last_name', ''),
                    'email': email,
                    'event_time': event.get('time', ''),
                    'event_type': message
                })
            else:
                print(f"    Event '{message}' doesn't match click/submit criteria")
        
        print(f"\nFinal Results:")
        print(f"  Affected users found: {len(affected_users)}")
        for user in affected_users:
            print(f"    - {user['email']}: {user['event_type']}")
        
        return affected_users
        
    except Exception as e:
        print(f"Error debugging campaign: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_campaign.py <campaign_id>")
        print("Example: python debug_campaign.py 12")
        sys.exit(1)
    
    try:
        campaign_id = int(sys.argv[1])
        debug_campaign_results(campaign_id)
    except ValueError:
        print("Error: Campaign ID must be a number")
        sys.exit(1)
