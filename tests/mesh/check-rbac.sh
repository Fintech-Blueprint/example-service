#!/bin/bash
# Validate RBAC rules between service-a and service-b
set -e

echo "🔐 Checking RBAC rules between service-a and service-b..."

# Get a pod name from service-a
POD=$(kubectl get pod -l app=service-a -o jsonpath='{.items[0].metadata.name}')
if [ -z "$POD" ]; then
    echo "❌ No service-a pods found"
    exit 1
fi

echo "🔍 Testing access from service-a to service-b..."

# Test endpoints with expected responses
endpoints=(
    "/health"        # Should return 200
    "/metrics"       # Should return 403 (RBAC denied)
    "/api/v1/data"   # Should return 403 (RBAC denied)
)

for endpoint in "${endpoints[@]}"; do
    echo "Testing endpoint: $endpoint"
    response=$(kubectl exec -it $POD -- curl -s -o /dev/null -w "%{http_code}" http://service-b:8080$endpoint)
    
    case $endpoint in
        "/health")
            if [ "$response" == "200" ]; then
                echo "✅ Health endpoint accessible as expected"
            else
                echo "❌ Health endpoint returned unexpected status: $response"
            fi
            ;;
        *)
            if [ "$response" == "403" ]; then
                echo "✅ RBAC correctly denying access to $endpoint"
            else
                echo "❌ RBAC validation failed for $endpoint - got $response, expected 403"
            fi
            ;;
    esac
done

echo "📋 Checking AuthorizationPolicy..."
kubectl get authorizationpolicy -n default -o yaml

echo "✅ RBAC validation complete. Check above output for any issues."