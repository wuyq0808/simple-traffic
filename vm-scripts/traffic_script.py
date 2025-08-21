import json
import datetime
from mitmproxy import http

def request(flow: http.HTTPFlow) -> None:
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "request",
        "method": flow.request.method,
        "url": flow.request.pretty_url,
        "headers": dict(flow.request.headers),
        "content": flow.request.content.decode('utf-8', errors='ignore') if flow.request.content else ""
    }
    
    with open("/tmp/traffic.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def response(flow: http.HTTPFlow) -> None:
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "response",
        "status_code": flow.response.status_code,
        "url": flow.request.pretty_url,
        "headers": dict(flow.response.headers),
        "content": flow.response.content.decode('utf-8', errors='ignore') if flow.response.content else ""
    }
    
    with open("/tmp/traffic.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")