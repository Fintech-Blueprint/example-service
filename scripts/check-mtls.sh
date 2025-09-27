#!/bin/bash
set -euo pipefail

echo "[INFO] Checking mTLS configuration..."

# Check PeerAuthentication policy
echo "[CHECK] PeerAuthentication in istio-system namespace..."
kubectl get peerauthentication -n istio-system -o yaml

# Check service-to-service mTLS status
echo "[CHECK] Service-to-service mTLS status..."
for ns in $(kubectl get ns -o jsonpath='{.items[*].metadata.name}'); do
    echo "Namespace: $ns"
    kubectl get pods -n $ns -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | while read pod; do
        if [[ ! -z "$pod" ]]; then
            echo "Pod: $pod"
            istioctl proxy-config authn "$pod" -n "$ns" || true
        fi
    done
done

# Check Destination Rules
echo "[CHECK] DestinationRules configuration..."
kubectl get destinationrules --all-namespaces -o yaml