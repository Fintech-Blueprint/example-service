#!/bin/bash
set -euo pipefail

echo "[INFO] Checking RBAC configuration..."

# Check ClusterRoles
echo "[CHECK] ClusterRoles..."
kubectl get clusterroles -o yaml

# Check ClusterRoleBindings
echo "[CHECK] ClusterRoleBindings..."
kubectl get clusterrolebindings -o yaml

# Check ServiceAccounts
echo "[CHECK] ServiceAccounts in all namespaces..."
kubectl get serviceaccounts --all-namespaces -o yaml

# Check Istio AuthorizationPolicies
echo "[CHECK] Istio AuthorizationPolicies..."
kubectl get authorizationpolicies --all-namespaces -o yaml