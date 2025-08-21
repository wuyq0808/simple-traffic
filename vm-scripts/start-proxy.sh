#!/bin/bash
echo "Starting traffic proxy on port 8080..."
echo "Log file: /tmp/traffic.jsonl"
echo "To stop: Press Ctrl+C"
echo ""
sudo -u traffic mitmdump -s /opt/traffic/traffic_script.py --set confdir=/opt/traffic/certs --listen-port 8080 --mode transparent