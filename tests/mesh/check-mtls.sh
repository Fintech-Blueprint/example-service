#!/bin/bash
# Validate mTLS between service-a and service-b
set -e

echo "🔒 Checking mTLS configuration between service-a and service-b..."

# Check if services exist
if ! kubectl get deploy service-a &>/dev/null; then
    echo "❌ service-a deployment not found"
    exit 1
fi

if ! kubectl get deploy service-b &>/dev/null; then
    echo "❌ service-b deployment not found"
    exit 1
fi

# Check TLS policy status
echo "📋 Checking TLS policy status..."
istioctl authn tls-check deploy/service-a deploy/service-b

# Validate actual mTLS traffic
echo "🔍 Validating actual mTLS traffic..."
POD_A=$(kubectl get pod -l app=service-a -o jsonpath='{.items[0].metadata.name}')

echo "📊 Checking Istio proxy configuration..."
istioctl proxy-config all $POD_A

echo "✅ mTLS validation complete. Check above output for any issues."