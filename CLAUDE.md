# Claude Code Notes

## VM Status Check

**Current VM:** `traffic-vm` in `us-central1-a`  
**External IP:** Dynamic (check with: `gcloud compute instances describe traffic-vm --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'`)

### Services Running
- **Go HTTP Proxy (simple-traffic container):** Port 8081 (HTTPS tunneling via CONNECT method)
- **Python Traffic Proxy:** Port 8080 (transparent proxy with mitmdump)

### Test Commands
```bash
# SSH into VM
gcloud compute ssh traffic-vm --zone=us-central1-a

# Check services on VM
docker ps | grep simple-traffic
pgrep -f mitmdump

# Check GCS bucket for traffic logs
gsutil ls gs://simple-relay-468808-api-responses-production/
```

### GCS Traffic Logs
- **Bucket:** `simple-relay-468808-api-responses-production` (configured in traffic_script.py)
- **Status:** Active with OAuth token logs captured
- **Note:** Traffic proxy uploads intercepted requests to this bucket

## GitHub Actions

### Manual-Only Workflows
- **`snapshot-vm.yml`** - Create VM snapshots with timestamp
- **`restore-vm-from-snapshot.yml`** - Restore VM from snapshot with optional service startup

### Auto-Deploy Workflow  
- **`deploy-traffic-vm.yml`** - Deploys on pushes to Go code (`cmd/**`, `internal/**`)
  - Ignores snapshot/restore workflow changes

## OAuth Token Extraction

**Script:** `python3 scripts/extract_oauth_tokens.py`  
**Output:** `oauth_token_details.txt` with complete OAuth flow details  
**Requirements:** Python 3.6+, gsutil configured  
**Note:** Scripts folder won't trigger GitHub workflows