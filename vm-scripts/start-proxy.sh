#!/bin/bash
echo "Starting traffic proxy on port 8080..."
echo "GCS bucket: $TRAFFIC_LOGS_BUCKET"
echo "To stop: Press Ctrl+C"
echo ""

# Load environment variables
source /etc/environment 2>/dev/null || true

# Export environment variables for the traffic script
export GCP_PROJECT_ID="$GCP_PROJECT_ID"
export TRAFFIC_LOGS_BUCKET="$TRAFFIC_LOGS_BUCKET"
export GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_APPLICATION_CREDENTIALS"

echo "Environment configured:"
echo "  GCP_PROJECT_ID: $GCP_PROJECT_ID"
echo "  TRAFFIC_LOGS_BUCKET: $TRAFFIC_LOGS_BUCKET"
echo "  GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
echo ""

sudo -u traffic -E mitmdump -s /opt/traffic/traffic_script.py --set confdir=/opt/traffic/certs --listen-port 8080 --mode transparent