#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <PROJECT_ID> <ZONE> <VM_NAME>"
  echo "Example: $0 my-gcp-project us-central1-a oracle-api-vm"
  exit 1
fi

PROJECT_ID="$1"
ZONE="$2"
VM_NAME="$3"
MACHINE_TYPE="${MACHINE_TYPE:-e2-micro}"
BOOT_DISK_SIZE_GB="${BOOT_DISK_SIZE_GB:-20}"
NETWORK_TAG="oracle-api"

gcloud config set project "$PROJECT_ID"

gcloud compute instances create "$VM_NAME" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --boot-disk-size="${BOOT_DISK_SIZE_GB}GB" \
  --boot-disk-type="pd-standard" \
  --image-family="debian-12" \
  --image-project="debian-cloud" \
  --tags="$NETWORK_TAG" \
  --scopes=https://www.googleapis.com/auth/cloud-platform

# Allow HTTP traffic to app port
gcloud compute firewall-rules create allow-oracle-8000 \
  --allow=tcp:8000 \
  --target-tags="$NETWORK_TAG" \
  --description="Allow inbound traffic to Project Oracle API" \
  || true

# Run bootstrap on VM
gcloud compute scp scripts/gcp/bootstrap_vm.sh "$VM_NAME":~/bootstrap_vm.sh --zone="$ZONE"
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="chmod +x ~/bootstrap_vm.sh && ~/bootstrap_vm.sh"

echo "VM ready. Test with:"
echo "  gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)'"
