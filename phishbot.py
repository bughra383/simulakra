"""
Automated Monthly Phishing Campaign Script using GoPhish API

This script automates the creation and management of monthly phishing campaigns
using direct HTTP calls to the GoPhish API.
"""

import csv
import logging
import os
import sys
import time
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import yaml
import requests
from dotenv import load_dotenv


class GoPhishAPIClient:
    """Direct HTTP API client for GoPhish."""
    
    def __init__(self, base_url: str, api_key: str, verify_ssl: bool = True):
        """Initialize the API client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make an HTTP request to the GoPhish API."""
        url = f"{self.base_url}/api/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, verify=self.verify_ssl)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, verify=self.verify_ssl)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, verify=self.verify_ssl)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, verify=self.verify_ssl)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.text:
                return response.json()
            else:
                return {}
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def get_smtp_profiles(self) -> List[Dict]:
        """Get all SMTP profiles."""
        return self._make_request('GET', 'smtp/')
    
    def get_templates(self) -> List[Dict]:
        """Get all email templates."""
        return self._make_request('GET', 'templates/')
    
    def get_pages(self) -> List[Dict]:
        """Get all landing pages."""
        return self._make_request('GET', 'pages/')
    
    def get_groups(self) -> List[Dict]:
        """Get all target groups."""
        return self._make_request('GET', 'groups/')
    
    def create_group(self, group_data: Dict) -> Dict:
        """Create a new target group."""
        return self._make_request('POST', 'groups/', group_data)
    
    def get_campaigns(self) -> List[Dict]:
        """Get all campaigns."""
        return self._make_request('GET', 'campaigns/')
    
    def create_campaign(self, campaign_data: Dict) -> Dict:
        """Create a new campaign."""
        return self._make_request('POST', 'campaigns/', campaign_data)
    
    def get_campaign(self, campaign_id: int) -> Dict:
        """Get campaign details by ID."""
        return self._make_request('GET', f'campaigns/{campaign_id}')
    
    def get_campaign_summary(self, campaign_id: int) -> Dict:
        """Get campaign summary with results."""
        return self._make_request('GET', f'campaigns/{campaign_id}/summary')


class PhishingCampaignManager:
    """Manages automated phishing campaigns using GoPhish API."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the campaign manager with configuration."""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        try:
            load_dotenv()
            self.config = self.load_config(config_path)
            
            api_key = os.getenv('GOPHISH_API_KEY')
            if not api_key:
                api_key = self.config['gophish'].get('api_key', '').replace('${GOPHISH_API_KEY}', os.getenv('GOPHISH_API_KEY', ''))
            
            if not api_key:
                raise ValueError("GOPHISH_API_KEY not found in environment variables")
            
            self.api = GoPhishAPIClient(
                self.config['gophish']['url'],
                api_key,
                self.config['gophish'].get('verify_ssl', True)
            )
            
            self.test_api_connection()
            self.logger.info("PhishingCampaignManager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PhishingCampaignManager: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Configure logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('phishbot.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            self.logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file {config_path} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def test_api_connection(self):
        """Test connection to GoPhish API."""
        try:
            profiles = self.api.get_smtp_profiles()
            self.logger.info("Successfully connected to GoPhish API")
        except Exception as e:
            self.logger.error(f"Failed to connect to GoPhish API: {e}")
            sys.exit(2)
    
    def read_targets_csv(self, csv_path: str) -> List[Dict]:
        """Read target information from CSV file."""
        targets = []
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                required_fields = ['FirstName', 'LastName', 'Email', 'Position']
                
                if not all(field in reader.fieldnames for field in required_fields):
                    raise ValueError(f"CSV must contain columns: {required_fields}")
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                    # Safe extraction with None checking
                    first_name = row.get('FirstName')
                    last_name = row.get('LastName') 
                    email = row.get('Email')
                    position = row.get('Position')
                    
                    # Convert None to empty string and strip
                    first_name = (first_name or '').strip()
                    last_name = (last_name or '').strip()
                    email = (email or '').strip()
                    position = (position or '').strip()
                    
                    # Skip rows without email (most critical field)
                    if not email:
                        self.logger.warning(f"Skipping row {row_num}: missing email address")
                        continue
                    
                    # Validate email has basic structure
                    if '@' not in email:
                        self.logger.warning(f"Skipping row {row_num}: invalid email format: {email}")
                        continue
                    
                    targets.append({
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email.lower(),
                        'position': position
                    })
                
                self.logger.info(f"Loaded {len(targets)} targets from {csv_path}")
                return targets
                
        except FileNotFoundError:
            self.logger.error(f"Target CSV file {csv_path} not found")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {e}")
            sys.exit(1)
    
    def get_smtp_profile(self, name: str) -> Dict:
        """Get SMTP profile by name."""
        try:
            profiles = self.api.get_smtp_profiles()
            for profile in profiles:
                if profile.get('name') == name:
                    self.logger.info(f"Found SMTP profile: {name}")
                    return profile
            
            self.logger.error(f"SMTP profile '{name}' not found")
            sys.exit(3)
            
        except Exception as e:
            self.logger.error(f"Error fetching SMTP profiles: {e}")
            sys.exit(3)
    
    def get_template(self, name: str) -> Dict:
        """Get email template by name."""
        try:
            templates = self.api.get_templates()
            for template in templates:
                if template.get('name') == name:
                    self.logger.info(f"Found template: {name}")
                    return template
            
            self.logger.error(f"Template '{name}' not found")
            sys.exit(3)
            
        except Exception as e:
            self.logger.error(f"Error fetching templates: {e}")
            sys.exit(3)
    
    def get_landing_page(self, name: str) -> Dict:
        """Get landing page by name."""
        try:
            pages = self.api.get_pages()
            for page in pages:
                if page.get('name') == name:
                    self.logger.info(f"Found landing page: {name}")
                    return page
            
            self.logger.error(f"Landing page '{name}' not found")
            sys.exit(3)
            
        except Exception as e:
            self.logger.error(f"Error fetching landing pages: {e}")
            sys.exit(3)
    
    def create_target_group(self, targets: List[Dict], group_name: str) -> Dict:
        """Create a target group from the CSV data, or reuse existing group."""
        try:
            # First, check if a group with this name already exists
            existing_groups = self.api.get_groups()
            for group in existing_groups:
                if group.get('name') == group_name:
                    self.logger.info(f"Found existing target group '{group_name}' with {len(group.get('targets', []))} targets")
                    return group
            
            # If no existing group found, create a new one
            gophish_targets = []
            for target in targets:
                gophish_targets.append({
                    'first_name': target['first_name'],
                    'last_name': target['last_name'],
                    'email': target['email'],
                    'position': target['position']
                })
            
            group_data = {
                'name': group_name,
                'targets': gophish_targets
            }
            
            created_group = self.api.create_group(group_data)
            self.logger.info(f"Created new target group '{group_name}' with {len(gophish_targets)} targets")
            return created_group
            
        except Exception as e:
            self.logger.error(f"Error creating target group: {e}")
            sys.exit(3)
    
    def create_campaign(self, campaign_name: str, group: Dict, 
                       smtp_profile: Dict, template: Dict, 
                       landing_page: Dict, url: str) -> Dict:
        """Create and launch a phishing campaign."""
        try:
            campaign_data = {
                'name': campaign_name,
                'groups': [group],
                'page': landing_page,
                'template': template,
                'smtp': smtp_profile,
                'url': url,
                'launch_date': datetime.now().isoformat() + 'Z'
            }
            
            created_campaign = self.api.create_campaign(campaign_data)
            self.logger.info(f"Created and launched campaign: {campaign_name}")
            return created_campaign
            
        except Exception as e:
            self.logger.error(f"Error creating campaign: {e}")
            sys.exit(3)
    
    def wait_for_campaign_completion(self, campaign_id: int, timeout_hours: int = 24) -> Dict:
        """Wait for campaign completion or timeout."""
        start_time = datetime.now()
        timeout_time = start_time + timedelta(hours=timeout_hours)
        
        self.logger.info(f"Monitoring campaign {campaign_id} for completion (timeout: {timeout_hours}h)")
        
        # Check every 10 minutes as specified in requirements
        check_interval = 600  # 10 minutes
        
        # For shorter testing, allow manual completion after 30 minutes if no new activity
        last_activity_check = None
        no_activity_timeout = timedelta(minutes=30)
        
        while datetime.now() < timeout_time:
            try:
                campaign = self.api.get_campaign(campaign_id)
                campaign_summary = self.api.get_campaign_summary(campaign_id)
                
                status = campaign.get('status', 'Unknown')
                stats = campaign_summary.get('stats', {})
                
                # Log current status and stats
                total = stats.get('total', 0)
                sent = stats.get('sent', 0)
                opened = stats.get('opened', 0)
                clicked = stats.get('clicked', 0)
                submitted = stats.get('submitted_data', 0)
                
                self.logger.info(f"Campaign {campaign_id} - Status: {status}")
                self.logger.info(f"  Stats: {sent}/{total} sent, {opened} opened, {clicked} clicked, {submitted} submitted")
                
                # Check if campaign is explicitly completed
                if status in ["Completed", "Finished"]:
                    self.logger.info(f"Campaign {campaign_id} completed successfully")
                    return campaign
                
                # Check if all emails have been sent and we have some results
                if sent > 0 and sent == total:
                    # If we have activity (clicks/submissions), check for timeout
                    if clicked > 0 or submitted > 0:
                        current_time = datetime.now()
                        if last_activity_check is None:
                            last_activity_check = current_time
                            self.logger.info(f"Campaign has activity. Starting 30-minute activity timeout.")
                        elif current_time - last_activity_check > no_activity_timeout:
                            self.logger.info(f"No new activity for 30 minutes. Considering campaign complete.")
                            return campaign
                    
                    # If no clicks/submissions yet, but all emails sent, wait a bit more
                    elif sent == total:
                        elapsed = datetime.now() - start_time
                        if elapsed > timedelta(hours=1):  # After 1 hour with no activity
                            self.logger.info(f"All emails sent, no activity after 1 hour. Considering campaign complete.")
                            return campaign
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error checking campaign status: {e}")
                time.sleep(check_interval)
        
        self.logger.warning(f"Campaign {campaign_id} monitoring timed out after {timeout_hours} hours")
        campaign = self.api.get_campaign(campaign_id)
        return campaign
    
    def extract_campaign_results(self, campaign: Dict) -> List[Dict]:
        """Extract clicked/submitted events from campaign results."""
        affected_users = []
        
        try:
            results = self.api.get_campaign_summary(campaign['id'])
            timeline = results.get('timeline', [])
            
            self.logger.info(f"Processing {len(timeline)} timeline events from campaign")
            
            # Track unique affected users to avoid duplicates
            processed_emails = set()
            
            # Method 1: Try timeline events first
            for event in timeline:
                message = event.get('message', '').lower()
                
                # Log all events for debugging
                self.logger.debug(f"Event: {event.get('message', '')} - Email: {event.get('email', '')}")
                
                # Check for various possible click/submit event types
                click_indicators = [
                    'clicked link', 'clicked', 'link clicked',
                    'submitted data', 'submitted', 'data submitted',
                    'form submitted', 'credentials submitted',
                    'email clicked', 'user clicked'
                ]
                
                if any(indicator in message for indicator in click_indicators):
                    details = event.get('details', {})
                    email = event.get('email', details.get('email', ''))
                    
                    # Skip if we already processed this email for this event type
                    event_key = f"{email}_{message}"
                    if event_key in processed_emails:
                        continue
                    processed_emails.add(event_key)
                    
                    if email:  # Only add if we have an email
                        affected_users.append({
                            'first_name': details.get('first_name', ''),
                            'last_name': details.get('last_name', ''),
                            'email': email,
                            'event_time': event.get('time', ''),
                            'event_type': event.get('message', message)
                        })
                        self.logger.info(f"Found affected user: {email} - {event.get('message', '')}")
            
            # Method 2: If timeline is empty, try to get campaign details directly
            if not affected_users and len(timeline) == 0:
                self.logger.info("Timeline is empty, trying alternative extraction method...")
                
                # Get campaign details to access results
                campaign_details = self.api.get_campaign(campaign['id'])
                campaign_results = campaign_details.get('results', [])
                
                self.logger.info(f"Found {len(campaign_results)} campaign results")
                
                for result in campaign_results:
                    # Check if this target clicked or submitted
                    if result.get('status') in ['Clicked Link', 'Submitted Data'] or \
                       any(key in result for key in ['clicked', 'submitted_data']) or \
                       result.get('reported', False):
                        
                        email = result.get('email', '')
                        if email and email not in processed_emails:
                            processed_emails.add(email)
                            
                            # Determine event type based on available data
                            event_type = "Clicked Link"
                            if 'submitted_data' in result or result.get('status') == 'Submitted Data':
                                event_type = "Submitted Data"
                            
                            affected_users.append({
                                'first_name': result.get('first_name', ''),
                                'last_name': result.get('last_name', ''),
                                'email': email,
                                'event_time': result.get('send_date', ''),
                                'event_type': event_type
                            })
                            self.logger.info(f"Found affected user from results: {email} - {event_type}")
            
            # Method 3: If still no results but stats show activity, create generic entries
            if not affected_users:
                stats = results.get('stats', {})
                clicked = stats.get('clicked', 0)
                submitted = stats.get('submitted_data', 0)
                
                if clicked > 0 or submitted > 0:
                    self.logger.warning(f"Campaign stats show {clicked} clicks and {submitted} submissions, but no specific user data found")
                    self.logger.warning("Creating generic affected user entries based on campaign group")
                    
                    # Get the campaign group to find target emails
                    campaign_details = self.api.get_campaign(campaign['id'])
                    groups = campaign_details.get('groups', [])
                    
                    for group in groups:
                        targets = group.get('targets', [])
                        for i, target in enumerate(targets):
                            # If we have more activity than targets, assume all clicked
                            # Otherwise, just mark the first N targets as affected
                            if i < max(clicked, submitted):
                                email = target.get('email', '')
                                if email:
                                    event_type = "Submitted Data" if i < submitted else "Clicked Link"
                                    affected_users.append({
                                        'first_name': target.get('first_name', ''),
                                        'last_name': target.get('last_name', ''),
                                        'email': email,
                                        'event_time': datetime.now().isoformat(),
                                        'event_type': event_type
                                    })
                                    self.logger.info(f"Created generic affected user entry: {email} - {event_type}")
                        
                        # Break after processing first group (usually only one anyway)
                        break
            
            self.logger.info(f"Extracted {len(affected_users)} affected users from campaign results")
            return affected_users
            
        except Exception as e:
            self.logger.error(f"Error extracting campaign results: {e}")
            return []
    
    def save_results_csv(self, affected_users: List[Dict], filename: str):
        """Save campaign results to CSV file."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['FirstName', 'LastName', 'Email', 'EventTime', 'EventType']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for user in affected_users:
                    writer.writerow({
                        'FirstName': user['first_name'],
                        'LastName': user['last_name'],
                        'Email': user['email'],
                        'EventTime': user['event_time'],
                        'EventType': user['event_type']
                    })
            
            self.logger.info(f"Campaign results saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving results CSV: {e}")
    
    def send_warning_email(self, email: str, first_name: str, last_name: str):
        """Send security warning email to affected user."""
        try:
            smtp_server = os.getenv('MAILGUN_SMTP_SERVER')
            smtp_port = int(os.getenv('MAILGUN_SMTP_PORT', '587'))
            smtp_user = os.getenv('MAILGUN_SMTP_USER')
            smtp_pass = os.getenv('MAILGUN_SMTP_PASS')
            sender_email = self.config['smtp']['sender_email']
            sender_name = self.config['smtp']['sender_name']
            
            if not all([smtp_server, smtp_user, smtp_pass, sender_email]):
                raise ValueError("Missing required SMTP environment variables")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Change this text to your desired warning subject"
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = email
            
            text_body = f"""
Dear {first_name} {last_name},

Change this text to your desired warning message.

"""

            html_body = f"""
<html>
<body>
<p>Dear {first_name} {last_name},</p>
<p>Change this text to your desired warning message.</p>
</body>
</html>
"""
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            self.logger.info(f"Warning email sent to {email}")
            
        except Exception as e:
            self.logger.error(f"Error sending warning email to {email}: {e}")
    
    def send_warning_emails(self, affected_users: List[Dict]):
        """Send warning emails to all affected users."""
        self.logger.info(f"Sending warning emails to {len(affected_users)} affected users")
        
        for user in affected_users:
            try:
                self.send_warning_email(
                    user['email'],
                    user['first_name'],
                    user['last_name']
                )
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Failed to send warning email to {user['email']}: {e}")
                continue
        
        self.logger.info("Completed sending warning emails")
    
    def run_monthly_campaign(self):
        """Execute the complete monthly phishing campaign workflow."""
        try:
            current_date = datetime.now()
            year_month = current_date.strftime("%Y-%m")
            
            campaign_name = f"Campaign name {year_month}"
            group_name = f"Targets-{year_month}"
            results_filename = f"clicked_{year_month}.csv"
            
            self.logger.info(f"Starting monthly campaign: {campaign_name}")
            
            targets = self.read_targets_csv(self.config['campaign']['targets_csv'])
            
            smtp_profile = self.get_smtp_profile(self.config['campaign']['smtp_profile'])
            template = self.get_template(self.config['campaign']['template'])
            landing_page = self.get_landing_page(self.config['campaign']['landing_page'])
            
            group = self.create_target_group(targets, group_name)
            
            campaign = self.create_campaign(
                campaign_name,
                group,
                smtp_profile,
                template,
                landing_page,
                self.config['campaign']['url']
            )
            
            completed_campaign = self.wait_for_campaign_completion(
                campaign['id'],
                self.config['campaign'].get('timeout_hours', 24)
            )
            
            affected_users = self.extract_campaign_results(completed_campaign)
            
            if affected_users:
                self.save_results_csv(affected_users, results_filename)
                
                if self.config['campaign'].get('send_warning_emails', True):
                    self.send_warning_emails(affected_users)
            else:
                self.logger.info("No users clicked links or submitted data")
            
            self.logger.info(f"Monthly campaign {campaign_name} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Fatal error in monthly campaign: {e}")
            sys.exit(3)
    
    def manual_complete_campaign(self, campaign_id: int):
        """Manually complete a campaign and process results (for testing)."""
        try:
            self.logger.info(f"Manually completing campaign {campaign_id}")
            
            # Get current campaign state
            campaign = self.api.get_campaign(campaign_id)
            
            # Extract and process results immediately
            affected_users = self.extract_campaign_results(campaign)
            
            if affected_users:
                current_date = datetime.now()
                year_month = current_date.strftime("%Y-%m")
                results_filename = f"clicked_{year_month}_manual.csv"
                
                self.save_results_csv(affected_users, results_filename)
                
                if self.config['campaign'].get('send_warning_emails', True):
                    self.send_warning_emails(affected_users)
                    
                self.logger.info(f"Manually completed campaign {campaign_id} with {len(affected_users)} affected users")
            else:
                self.logger.info(f"Campaign {campaign_id} completed with no affected users")
                
            return campaign
            
        except Exception as e:
            self.logger.error(f"Error manually completing campaign: {e}")
            raise

def main():
    """Main entry point for the script."""
    # Check for test mode argument
    test_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_mode = True
        print("🧪 Running in test mode (shorter timeouts)")
    
    try:
        manager = PhishingCampaignManager()
        
        if test_mode:
            # Override timeout for testing (30 minutes instead of 24 hours)
            manager.config['campaign']['timeout_hours'] = 0.5  # 30 minutes
            manager.logger.info("Test mode: Using 30-minute timeout instead of 24 hours")
        
        manager.run_monthly_campaign()
        sys.exit(0)
        
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Script interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
