#!/usr/bin/env python3

import json
import re
from collections import defaultdict

def analyze_traffic_log(filename):
    """Analyze Claude Code inference requests from traffic log"""
    
    inference_requests = []
    anthropic_requests = []
    
    with open(filename, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                
                # Filter for Anthropic API requests
                if 'api.anthropic.com' in entry.get('url', ''):
                    anthropic_requests.append(entry)
                    
                    # Look for inference requests (messages endpoint)
                    if '/v1/messages' in entry.get('url', '') and entry.get('type') == 'request':
                        inference_requests.append(entry)
                        
            except json.JSONDecodeError:
                continue
    
    print("=== CLAUDE CODE INFERENCE ANALYSIS ===\n")
    
    print(f"📊 Total Anthropic API requests: {len(anthropic_requests)}")
    print(f"🧠 Inference requests found: {len(inference_requests)}\n")
    
    # Analyze each inference request
    for i, req in enumerate(inference_requests, 1):
        print(f"--- INFERENCE REQUEST #{i} ---")
        print(f"⏰ Timestamp: {req['timestamp']}")
        print(f"🔗 URL: {req['url']}")
        
        # Parse request content
        try:
            content = json.loads(req['content'])
            
            print(f"🤖 Model: {content.get('model', 'unknown')}")
            print(f"🎯 Max tokens: {content.get('max_tokens', 'unknown')}")
            print(f"🌡️ Temperature: {content.get('temperature', 'unknown')}")
            print(f"📝 Stream: {content.get('stream', False)}")
            
            # Extract user message
            messages = content.get('messages', [])
            if messages:
                user_msg = messages[0].get('content', '')
                if isinstance(user_msg, list):
                    # Handle content arrays
                    text_parts = [part.get('text', '') for part in user_msg if part.get('type') == 'text']
                    user_msg = ' '.join(text_parts)
                
                print(f"💬 User message: {user_msg[:100]}..." if len(user_msg) > 100 else f"💬 User message: {user_msg}")
            
            # Check for special metadata
            metadata = content.get('metadata', {})
            if metadata:
                print(f"📋 Metadata: {metadata}")
                
            # Extract headers
            headers = req.get('headers', {})
            auth_header = headers.get('authorization', '')
            if auth_header:
                print(f"🔐 Auth: {auth_header[:20]}...")
                
            # Look for beta features
            beta_header = headers.get('anthropic-beta', '')
            if beta_header:
                print(f"🧪 Beta features: {beta_header}")
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Error parsing request content: {e}")
        
        print()
    
    # Find corresponding responses
    print("=== RESPONSE ANALYSIS ===\n")
    
    for i, req in enumerate(inference_requests, 1):
        req_timestamp = req['timestamp']
        
        # Find response within reasonable time window (next few entries)
        for line in open(filename, 'r'):
            try:
                entry = json.loads(line.strip())
                if (entry.get('type') == 'response' and 
                    '/v1/messages' in entry.get('url', '') and
                    entry['timestamp'] > req_timestamp):
                    
                    print(f"--- RESPONSE FOR REQUEST #{i} ---")
                    print(f"⏰ Timestamp: {entry['timestamp']}")
                    print(f"📊 Status: {entry['status_code']}")
                    
                    # Parse response headers for rate limiting info
                    headers = entry.get('headers', {})
                    for header, value in headers.items():
                        if 'ratelimit' in header.lower():
                            print(f"⚡ {header}: {value}")
                    
                    # Parse response content (truncated for analysis)
                    content = entry.get('content', '')
                    if content and not content.startswith('event:'):  # Skip streaming responses
                        try:
                            resp_data = json.loads(content)
                            usage = resp_data.get('usage', {})
                            if usage:
                                print(f"📈 Token usage: {usage}")
                                
                            model = resp_data.get('model', '')
                            if model:
                                print(f"🤖 Response model: {model}")
                                
                        except json.JSONDecodeError:
                            print(f"📄 Response content length: {len(content)} chars")
                    
                    print()
                    break
                    
            except json.JSONDecodeError:
                continue
    
    # Analyze authentication and session info
    print("=== AUTHENTICATION & SESSION ANALYSIS ===\n")
    
    auth_patterns = set()
    user_agents = set()
    
    for req in anthropic_requests:
        if req.get('type') == 'request':
            headers = req.get('headers', {})
            
            # Extract auth patterns
            auth = headers.get('authorization', '')
            if auth:
                # Extract token type and prefix
                if auth.startswith('Bearer sk-ant-'):
                    auth_patterns.add('Bearer sk-ant-oat01-*')
                
            # Extract user agents
            ua = headers.get('user-agent', '')
            if ua:
                user_agents.add(ua)
    
    print("🔐 Authentication patterns:")
    for pattern in auth_patterns:
        print(f"  - {pattern}")
    
    print("\n🖥️ User agents:")
    for ua in user_agents:
        print(f"  - {ua}")
    
    # Look for telemetry/statsig requests
    print("\n=== TELEMETRY ANALYSIS ===\n")
    
    statsig_requests = [req for req in anthropic_requests if 'statsig.anthropic.com' in req.get('url', '')]
    print(f"📊 Statsig telemetry requests: {len(statsig_requests)}")
    
    if statsig_requests:
        # Analyze telemetry events
        events = defaultdict(int)
        for req in statsig_requests:
            if req.get('type') == 'request':
                try:
                    content = json.loads(req['content'])
                    for event in content.get('events', []):
                        event_name = event.get('eventName', 'unknown')
                        events[event_name] += 1
                except (json.JSONDecodeError, KeyError):
                    continue
        
        print("📈 Telemetry events:")
        for event, count in sorted(events.items()):
            print(f"  - {event}: {count}")

if __name__ == "__main__":
    analyze_traffic_log("traffic.jsonl")