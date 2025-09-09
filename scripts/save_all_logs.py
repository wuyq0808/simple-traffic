#!/usr/bin/env python3
"""
Save All Logs Script

Downloads all traffic logs from GCS bucket and saves them to local folder.
"""

import subprocess
import tempfile
import shutil
import os


def run_command(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Error: {result.stderr}")
        return None
    return result.stdout.strip()


def main():
    print("Save All Logs Script")
    print("Downloading all traffic logs to downloaded_logs folder...")
    
    # Download directly to the target folder
    cmd = 'gsutil -m cp -r "gs://simple-relay-468808-api-responses-production/traffic-logs/" "downloaded_logs/"'
    result = run_command(cmd)
    
    if result is None:
        print("Failed to download logs")
        return 1
    
    print("Download completed!")
    print(f"Files saved to: downloaded_logs/traffic-logs/")
    
    # List what we got
    list_cmd = "ls -la downloaded_logs/traffic-logs/ | wc -l"
    count = run_command(list_cmd)
    if count:
        print(f"Downloaded {int(count) - 1} files")
    
    return 0


if __name__ == "__main__":
    exit(main())