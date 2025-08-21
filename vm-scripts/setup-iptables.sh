#!/bin/bash
echo "Setting up iptables rules for transparent interception..."
# Exclude traffic user from redirection to prevent loops
sudo iptables -t nat -A OUTPUT -m owner --uid-owner traffic -j RETURN
# Redirect HTTP traffic to mitmproxy
sudo iptables -t nat -A OUTPUT -p tcp --dport 80 -j REDIRECT --to-port 8080
# Redirect HTTPS traffic to mitmproxy
sudo iptables -t nat -A OUTPUT -p tcp --dport 443 -j REDIRECT --to-port 8080
echo "iptables rules configured for transparent mode"