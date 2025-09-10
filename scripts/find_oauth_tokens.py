#!/usr/bin/env python3

import os
import json
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(command):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def download_host_logs(host, output_dir="host_logs"):
    """Download all logs for a specific host"""
    print(f"Downloading logs for host: {host}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Download logs for specific host
    bucket_path = f"gs://simple-relay-468808-api-responses-production/traffic-logs/{host}/"
    local_path = f"{output_dir}/{host}/"
    
    command = f'gsutil -m cp -r "{bucket_path}" "{output_dir}/"'
    result = run_command(command)
    
    if result is None:
        print(f"Failed to download logs for {host}")
        return None
    
    print(f"Downloaded logs to: {local_path}")
    return local_path

def scan_for_oauth_tokens(log_directory):
    """Scan log files specifically for OAuth token responses with both access_token and refresh_token"""
    results = []
    
    if not os.path.exists(log_directory):
        print(f"Directory not found: {log_directory}")
        return results
    
    print(f"Scanning directory: {log_directory}")
    
    # Find all JSON files
    json_files = list(Path(log_directory).glob("*.json"))
    print(f"Found {len(json_files)} JSON files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Only look for response files with oauth/token endpoint
            url = data.get('url', '')
            if not ('oauth/token' in url.lower() and data.get('type') == 'response'):
                continue
            
            # Check content for both access_token and refresh_token
            content = data.get('content', '')
            if content:
                try:
                    content_json = json.loads(content)
                    
                    # Must have BOTH access_token AND refresh_token
                    has_access_token = 'access_token' in content_json
                    has_refresh_token = 'refresh_token' in content_json
                    
                    if has_access_token and has_refresh_token:
                        oauth_indicators = [
                            f"OAuth URL: {url}",
                            f"Access Token: {content_json['access_token'][:20]}...",
                            f"Refresh Token: {content_json['refresh_token'][:20]}..."
                        ]
                        
                        # Add additional token info if available
                        if 'expires_in' in content_json:
                            oauth_indicators.append(f"Expires in: {content_json['expires_in']} seconds")
                        if 'scope' in content_json:
                            oauth_indicators.append(f"Scope: {content_json['scope']}")
                        if 'organization' in content_json:
                            org_name = content_json['organization'].get('name', 'N/A')
                            oauth_indicators.append(f"Organization: {org_name}")
                        if 'account' in content_json:
                            email = content_json['account'].get('email_address', 'N/A')
                            oauth_indicators.append(f"Account: {email}")
                        
                        results.append({
                            'file': str(json_file),
                            'relative_path': json_file.name,
                            'timestamp': data.get('timestamp', ''),
                            'method': data.get('method', ''),
                            'url': data.get('url', ''),
                            'type': data.get('type', ''),
                            'status_code': data.get('status_code', ''),
                            'oauth_indicators': oauth_indicators,
                            'access_token': content_json['access_token'],
                            'refresh_token': content_json['refresh_token']
                        })
                        
                except json.JSONDecodeError:
                    continue
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Download and scan traffic logs for OAuth tokens')
    parser.add_argument('host', help='Host IP or domain to download logs for')
    parser.add_argument('--output-dir', default='host_logs', help='Output directory for downloaded logs')
    
    args = parser.parse_args()
    
    # Download logs for the specified host
    log_directory = download_host_logs(args.host, args.output_dir)
    
    if log_directory is None:
        print("Failed to download logs")
        sys.exit(1)
    
    # Scan for OAuth tokens
    oauth_results = scan_for_oauth_tokens(log_directory)
    
    if not oauth_results:
        print(f"No OAuth token response files found in logs for {args.host}")
        print("Looking specifically for oauth/token endpoint responses with both access_token and refresh_token")
        return
    
    print(f"\n=== OAuth Token Response Files for {args.host} ===")
    print(f"Found {len(oauth_results)} files with complete OAuth tokens:")
    
    for i, result in enumerate(oauth_results, 1):
        print(f"\n🔑 TOKEN FILE #{i}")
        print(f"   File: {result['relative_path']}")
        print(f"   Full path: {result['file']}")
        print("="*80)
        
        # Read and pretty print the complete JSON file
        try:
            with open(result['file'], 'r') as f:
                complete_data = json.load(f)
            
            # Pretty print the entire JSON
            print(json.dumps(complete_data, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"Error reading file {result['file']}: {e}")
        
        print("="*80)

if __name__ == "__main__":
    main()