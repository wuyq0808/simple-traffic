#!/bin/bash
echo "Clearing traffic logs..."
sudo rm -f /tmp/traffic.jsonl
sudo touch /tmp/traffic.jsonl
sudo chmod 666 /tmp/traffic.jsonl
echo "Traffic logs cleared"