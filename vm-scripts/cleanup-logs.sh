#!/bin/bash
echo "Clearing traffic logs..."
sudo -u traffic rm -f /opt/traffic/logs/traffic.jsonl
sudo -u traffic touch /opt/traffic/logs/traffic.jsonl
echo "Traffic logs cleared"