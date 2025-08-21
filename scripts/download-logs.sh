#!/bin/bash

# Download traffic logs from GCP VM
# This script downloads the traffic.jsonl file from /opt/traffic/logs/ on the VM

set -e

# Configuration
VM_NAME="traffic-vm"
ZONE="us-central1-a"
PROJECT_ID="simple-relay-468808"
REMOTE_LOG_PATH="/opt/traffic/logs/traffic.jsonl"
LOCAL_LOG_PATH="./traffic.jsonl"

echo "Downloading traffic logs from VM: $VM_NAME"
echo "Remote path: $REMOTE_LOG_PATH"
echo "Local path: $LOCAL_LOG_PATH"
echo ""

# Check if VM exists and is running
echo "Checking VM status..."
VM_STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID --format="value(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$VM_STATUS" = "NOT_FOUND" ]; then
    echo "Error: VM $VM_NAME not found in zone $ZONE"
    exit 1
elif [ "$VM_STATUS" != "RUNNING" ]; then
    echo "Warning: VM is in status: $VM_STATUS"
    echo "Attempting to download anyway..."
fi

# Download the log file using gcloud compute scp
echo "Downloading log file..."
gcloud compute scp $VM_NAME:$REMOTE_LOG_PATH $LOCAL_LOG_PATH \
    --zone=$ZONE \
    --project=$PROJECT_ID \
    --scp-flag="-o StrictHostKeyChecking=no"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Download completed successfully!"
    echo "Log file saved to: $LOCAL_LOG_PATH"
    
    # Show basic file info
    if [ -f "$LOCAL_LOG_PATH" ]; then
        FILE_SIZE=$(wc -c < "$LOCAL_LOG_PATH")
        LINE_COUNT=$(wc -l < "$LOCAL_LOG_PATH")
        echo "File size: $FILE_SIZE bytes"
        echo "Number of log entries: $LINE_COUNT"
        
        echo ""
        echo "First 3 lines of the log:"
        head -3 "$LOCAL_LOG_PATH" | jq -r . 2>/dev/null || head -3 "$LOCAL_LOG_PATH"
    fi
else
    echo "❌ Download failed!"
    echo "Make sure:"
    echo "1. You are authenticated with gcloud (run: gcloud auth login)"
    echo "2. The VM is running"
    echo "3. You have SSH access to the VM"
    echo "4. The log file exists on the VM"
    exit 1
fi