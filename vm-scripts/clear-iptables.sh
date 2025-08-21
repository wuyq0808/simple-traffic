#!/bin/bash
echo "Clearing iptables OUTPUT rules..."
sudo iptables -t nat -F OUTPUT
echo "iptables OUTPUT rules cleared - traffic interception disabled"