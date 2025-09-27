#!/usr/bin/env bash
set -euo pipefail

# Enhanced mesh validation script - validates mTLS and RBAC
# Store this as validate-mesh.sh

log_info() {
    echo "ℹ️ $1"
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
}

validate_mtls() {
    local ns="$1"
    log_info "Checking mTLS policy in namespace: $ns"
    
    # Check PeerAuthentication policy
    if kubectl get peerauthentication -n "$ns" default -o jsonpath='{.spec.mtls.mode}' 2>/dev/null | grep -q "STRICT"; then
        log_success "STRICT mTLS policy found"
    else
        log_error "STRICT mTLS policy not found"
        return 1
    fi

    # Check if workloads have Istio proxy
    local pods_with_proxy
    pods_with_proxy=$(kubectl get pods -n "$ns" -o jsonpath='{.items[*].status.containerStatuses[*].name}' | tr ' ' '\n' | grep -c "istio-proxy" || true)
    if [ "$pods_with_proxy" -gt 0 ]; then
        log_success "Found $pods_with_proxy pods with Istio proxy"
    else
        log_error "No pods with Istio proxy found"
        return 1
    fi

    return 0
}

validate_rbac() {
    local ns="$1"
    log_info "Checking RBAC policies in namespace: $ns"
    
    # Check AuthorizationPolicy
    if kubectl get authorizationpolicy -n "$ns" -o name | grep -q "service-mesh-policy"; then
        log_success "Authorization policy found"
        
        # Check policy details
        local policy_spec
        policy_spec=$(kubectl get authorizationpolicy -n "$ns" service-mesh-policy -o jsonpath='{.spec}')
        if echo "$policy_spec" | grep -q "ALLOW"; then
            log_success "Authorization policy has ALLOW action"
        else
            log_error "Authorization policy missing ALLOW action"
            return 1
        fi
    else
        log_error "No authorization policy found"
        return 1
    fi

    return 0
}

validate_mesh_config() {
    log_info "Validating mesh configuration..."
    
    # Check core Istio components
    log_info "Checking Istio control plane..."
    if ! kubectl get pods -n istio-system -l app=istiod -o jsonpath='{.items[*].status.phase}' | grep -q "Running"; then
        log_error "Istiod not running"
        return 1
    fi
    log_success "Istiod is running"

    # Check proxy status
    log_info "Checking proxy status..."
    if ! istioctl proxy-status | grep -q "SYNCED"; then
        log_error "Not all proxies are synced"
        return 1
    fi
    log_success "All proxies are synced"

    return 0
}

main() {
    local ns="${1:-default}"
    local exit_code=0

    log_info "Starting mesh validation for namespace: $ns"
    log_info "===================="

    validate_mesh_config || exit_code=$?
    echo ""
    
    validate_mtls "$ns" || exit_code=$?
    echo ""
    
    validate_rbac "$ns" || exit_code=$?
    echo ""

    if [ $exit_code -eq 0 ]; then
        log_success "All validations passed!"
    else
        log_error "Some validations failed"
    fi

    return $exit_code
}

main "$@"