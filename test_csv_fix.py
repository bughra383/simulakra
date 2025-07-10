#!/usr/bin/env python3
"""
Test script to debug and fix CSV reading issues
"""

import csv
import sys
from typing import List, Dict

def read_targets_csv_fixed(csv_path: str) -> List[Dict]:
    """Read target information from CSV file with improved error handling."""
    targets = []
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            required_fields = ['FirstName', 'LastName', 'Email', 'Position']
            
            if not all(field in reader.fieldnames for field in required_fields):
                raise ValueError(f"CSV must contain columns: {required_fields}")
            
            print(f"CSV columns found: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                print(f"Processing row {row_num}: {row}")
                
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
                
                print(f"  Parsed: FirstName='{first_name}', LastName='{last_name}', Email='{email}', Position='{position}'")
                
                # Skip rows without email (most critical field)
                if not email:
                    print(f"  -> Skipping row {row_num}: missing email address")
                    continue
                
                # Validate email has basic structure
                if '@' not in email:
                    print(f"  -> Skipping row {row_num}: invalid email format: {email}")
                    continue
                
                target = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email.lower(),
                    'position': position
                }
                targets.append(target)
                print(f"  -> Added target: {target}")
            
            print(f"Successfully loaded {len(targets)} targets")
            return targets
            
    except FileNotFoundError:
        print(f"Target CSV file {csv_path} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("Testing CSV reading with targets.csv...")
    targets1 = read_targets_csv_fixed("targets.csv")
    print(f"\nTargets from targets.csv: {len(targets1)}")
    
    print("\n" + "="*50)
    print("Testing CSV reading with test_targets.csv...")
    targets2 = read_targets_csv_fixed("test_targets.csv")
    print(f"\nTargets from test_targets.csv: {len(targets2)}")
