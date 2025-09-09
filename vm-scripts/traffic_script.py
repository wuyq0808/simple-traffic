import json
import datetime
import os
import uuid
from mitmproxy import http
from google.cloud import storage

class TrafficLogger:
    def __init__(self):
        """Initialize the traffic logger with GCS configuration"""
        # Get configuration from environment variables
        self.bucket_name = os.getenv('TRAFFIC_LOGS_BUCKET', 'simple-relay-468808-api-responses-production')
        self.project_id = os.getenv('GCP_PROJECT_ID', 'simple-relay-468808')
        
        # URL patterns to exclude from logging
        self.excluded_url_patterns = [
            '/computeMetadata/',  # Any metadata server requests
            'enable-workload-certificate',  # Failed workload cert requests
            'oslogin/users',  # OS Login requests
            'oslogin/groups',  # OS Login requests
        ]
        
        try:
            # Initialize GCS client
            self.gcs_client = storage.Client(project=self.project_id)
            self.bucket = self.gcs_client.bucket(self.bucket_name)
        except Exception as e:
            print(f"Error initializing GCS client: {e}")
            self.gcs_client = None
            self.bucket = None

    def upload_to_gcs(self, log_entry, host):
        """Upload single log entry directly to GCS"""
        if not self.bucket:
            return
            
        try:
            # Create unique blob name with host folder
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            # Sanitize host for use as folder name (replace special chars)
            safe_host = host.replace(':', '_').replace('/', '_')
            blob_name = f"traffic-logs/{safe_host}/{timestamp}_{unique_id}_{log_entry['type']}.json"
            
            blob = self.bucket.blob(blob_name)
            
            # Upload log entry
            blob.upload_from_string(
                json.dumps(log_entry),
                content_type='application/json'
            )
            
            # Set metadata
            blob.metadata = {
                'source': 'mitmproxy-traffic-script',
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'type': log_entry['type']
            }
            blob.patch()
            
        except Exception as e:
            print(f"Error uploading to GCS: {e}")

    def should_exclude_request(self, url):
        """Check if request should be excluded from logging"""
        # Check if URL contains any excluded patterns
        for pattern in self.excluded_url_patterns:
            if pattern in url:
                return True
                
        return False

    def request(self, flow: http.HTTPFlow) -> None:
        # Check if this request should be excluded
        if self.should_exclude_request(flow.request.pretty_url):
            return
            
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "request",
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "headers": dict(flow.request.headers),
            "content": flow.request.content.decode('utf-8', errors='ignore') if flow.request.content else ""
        }
        
        # Extract host from the request
        host = flow.request.host
        self.upload_to_gcs(log_entry, host)

    def response(self, flow: http.HTTPFlow) -> None:
        # Check if this response should be excluded
        if self.should_exclude_request(flow.request.pretty_url):
            return
            
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "response",
            "status_code": flow.response.status_code,
            "url": flow.request.pretty_url,
            "headers": dict(flow.response.headers),
            "content": flow.response.content.decode('utf-8', errors='ignore') if flow.response.content else ""
        }
        
        # Extract host from the request
        host = flow.request.host
        self.upload_to_gcs(log_entry, host)

# Register the addon
addons = [TrafficLogger()]