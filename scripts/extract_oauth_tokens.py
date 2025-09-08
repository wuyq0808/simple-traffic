#!/usr/bin/env python3
"""
OAuth Token Extraction Script

Downloads all traffic logs from GCS bucket and extracts the latest OAuth token information.
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


def run_command(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Error: {result.stderr}")
        return None
    return result.stdout.strip()


def download_logs():
    """Download all traffic logs to temporary directory"""
    temp_dir = tempfile.mkdtemp(prefix="traffic-logs-")
    print(f"Downloading logs to: {temp_dir}")
    
    cmd = f'gsutil -m cp -r "gs://simple-relay-468808-api-responses-production/traffic-logs/" "{temp_dir}/"'
    result = run_command(cmd)
    
    if result is None:
        print("Failed to download logs")
        return None
    
    return temp_dir


def extract_oauth_data(log_dir):
    """Extract OAuth token data from downloaded logs"""
    oauth_requests = []
    oauth_responses = []
    
    logs_path = Path(log_dir) / "traffic-logs"
    
    if not logs_path.exists():
        print(f"Logs directory not found: {logs_path}")
        return None, None
    
    # Search through all JSON files
    for json_file in logs_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Check if it's an OAuth-related request/response
            url = data.get('url', '')
            
            if 'console.anthropic.com' in url and 'oauth' in url:
                if data.get('type') == 'request':
                    oauth_requests.append({
                        'file': json_file.name,
                        'timestamp': data.get('timestamp'),
                        'data': data
                    })
                elif data.get('type') == 'response':
                    oauth_responses.append({
                        'file': json_file.name,
                        'timestamp': data.get('timestamp'),
                        'data': data
                    })
                    
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading {json_file}: {e}")
            continue
    
    return oauth_requests, oauth_responses


def find_latest_token_exchange(requests, responses):
    """Find the latest OAuth token exchange"""
    
    # Find token exchange requests (POST to /oauth/token)
    token_requests = []
    for req in requests:
        data = req['data']
        if (data.get('method') == 'POST' and 
            '/oauth/token' in data.get('url', '')):
            token_requests.append(req)
    
    if not token_requests:
        print("No OAuth token requests found")
        return None, None
    
    # Sort by timestamp to get the latest
    token_requests.sort(key=lambda x: x['timestamp'], reverse=True)
    latest_request = token_requests[0]
    
    # Find corresponding response
    req_timestamp = datetime.fromisoformat(latest_request['timestamp'].replace('Z', '+00:00'))
    
    # Look for response within 5 seconds after request
    matching_response = None
    for resp in responses:
        if '/oauth/token' in resp['data'].get('url', ''):
            resp_timestamp = datetime.fromisoformat(resp['timestamp'].replace('Z', '+00:00'))
            if resp_timestamp > req_timestamp and (resp_timestamp - req_timestamp).seconds <= 5:
                if not matching_response or resp_timestamp < datetime.fromisoformat(matching_response['timestamp'].replace('Z', '+00:00')):
                    matching_response = resp
    
    return latest_request, matching_response


def print_oauth_details(request, response, output_file=None):
    """Print detailed OAuth information and optionally save to file"""
    output = []
    
    output.append("="*80)
    output.append("LATEST OAUTH TOKEN EXCHANGE")
    output.append("="*80)
    
    if request:
        output.append(f"\n📤 REQUEST ({request['file']})")
        output.append(f"Timestamp: {request['timestamp']}")
        req_data = request['data']
        output.append(f"Method: {req_data.get('method')}")
        output.append(f"URL: {req_data.get('url')}")
        
        # Add all request headers
        headers = req_data.get('headers', {})
        if headers:
            output.append("\n📋 REQUEST HEADERS:")
            for key, value in headers.items():
                output.append(f"  {key}: {value}")
        
        # Parse request content
        try:
            content = json.loads(req_data.get('content', '{}'))
            output.append(f"\n📤 REQUEST CONTENT:")
            for key, value in content.items():
                output.append(f"  {key}: {value}")
        except json.JSONDecodeError:
            output.append("Could not parse request content")
    
    if response:
        output.append(f"\n📥 RESPONSE ({response['file']})")
        output.append(f"Timestamp: {response['timestamp']}")
        resp_data = response['data']
        output.append(f"Status Code: {resp_data.get('status_code')}")
        
        # Add all response headers
        headers = resp_data.get('headers', {})
        if headers:
            output.append("\n📋 RESPONSE HEADERS:")
            for key, value in headers.items():
                output.append(f"  {key}: {value}")
        
        # Parse response content
        try:
            content = json.loads(resp_data.get('content', '{}'))
            output.append(f"\n🔑 COMPLETE RESPONSE CONTENT:")
            output.append(json.dumps(content, indent=2))
            
        except json.JSONDecodeError:
            output.append("Could not parse response content")
    
    output.append("\n" + "="*80)
    
    # Print to console
    for line in output:
        print(line)
    
    # Save to file if specified
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write('\n'.join(output))
            print(f"\nDetails saved to: {output_file}")
        except IOError as e:
            print(f"Error saving to file: {e}")


def cleanup_temp_dir(temp_dir):
    """Clean up temporary directory"""
    if temp_dir and os.path.exists(temp_dir):
        run_command(f'rm -rf "{temp_dir}"')
        print(f"Cleaned up temporary directory: {temp_dir}")


def main():
    print("OAuth Token Extraction Script")
    print("Downloading all traffic logs and extracting OAuth tokens...")
    
    # Download logs
    temp_dir = download_logs()
    if not temp_dir:
        return 1
    
    try:
        # Extract OAuth data
        requests, responses = extract_oauth_data(temp_dir)
        
        if not requests and not responses:
            print("No OAuth traffic found in logs")
            return 1
        
        print(f"Found {len(requests)} OAuth requests and {len(responses)} OAuth responses")
        
        # Find latest token exchange
        latest_req, latest_resp = find_latest_token_exchange(requests, responses)
        
        if not latest_req:
            print("No OAuth token exchange found")
            return 1
        
        # Print details and save to file
        output_file = "oauth_token_details.txt"
        print_oauth_details(latest_req, latest_resp, output_file)
        
        return 0
        
    finally:
        cleanup_temp_dir(temp_dir)


if __name__ == "__main__":
    exit(main())