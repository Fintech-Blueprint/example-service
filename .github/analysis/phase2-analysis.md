# Phase 2 Requirements Analysis - Contradictions and Gray Zones

## 1. Implementation Conflicts

### Resource Management
**Contradiction Found:**
- Current sandbox mode retains runs in `reports/<feature-sha>/`
- New structure shows `services/service-a/` but unclear where reports go
- **Impact:** Need to clarify if reports stay at root or move under each service

### Retry Mechanism Ambiguity
**Gray Zone:**
- Current implementation: 2 retries, 120s intervals
- New monitoring requires tracking "success after 1st/2nd attempt"
- **Impact:** Need to clarify if retry timing changes based on monitoring feedback

### Security Implementation
**Contradiction Found:**
- Current: "Sandbox: Optional with warnings"
- New: "Basic vulnerability scan (still sandbox = optional)"
- But also: "Block merges unless: lint ✅, tests ✅, SAST ✅, signatures ✅"
- **Impact:** Unclear if SAST becomes mandatory in sandbox mode

## 2. Unclear Specifications

### Directory Structure
```
Current:
reports/
  <feature-sha>/
    <run-id>/

New Proposed:
services/
  service-a/
  service-b/
reports/
  ...

Golden Goose Output:
golden-goose/
  <feature-sha>/
    reports/
    artifacts/
    summary.txt
```
**Gray Zone:** Need to clarify:
- Where do service-specific reports go?
- How to handle feature-sha across multiple services?
- Relationship between reports/ and golden-goose/ directories

### Mode Switching
**Gray Zone:**
- When does a service switch from sandbox to compliance?
- Can services be in different modes simultaneously?
- How to handle dependencies between services in different modes?

## 3. Critical Missing Details

### 1. Multi-Service Implementation
- How to handle shared resources between services
- Cross-service dependency management
- Service-specific vs. global configuration precedence

### 2. Golden Goose Packaging
- Versioning strategy for the package
- Backup/rollback mechanism
- Artifact retention policy across multiple services

### 3. Monitoring Implementation
- Specific threshold values for alerts
- Storage duration for metrics
- Aggregation strategy for multi-service metrics

## 4. Recommended Clarifications Needed

### 1. Directory Structure
**Proposed Solution:**
```
root/
  services/
    service-a/
      reports/
        <feature-sha>/
    service-b/
      reports/
        <feature-sha>/
  golden-goose/
    releases/
      v1/
        <timestamp>/
          reports/
          artifacts/
  org-config.yaml
```

### 2. Mode Management
**Proposed Rules:**
1. Services default to sandbox mode
2. Compliance mode activation requires:
   - All dependencies in compliance mode
   - Full test coverage
   - SAST passing
   - Manual approval

### 3. Monitoring Structure
**Proposed Implementation:**
```yaml
monitoring:
  global:
    retention: 30d
    metrics:
      - deployment_success
      - retry_patterns
      - resource_usage
  service_specific:
    retention: 7d
    metrics:
      - service_health
      - dependency_health
```

## 5. Risk Assessment

### High Risk Areas
1. **Service Interdependencies**
   - Risk: Cascading failures
   - Need: Clear dependency mapping

2. **Resource Contention**
   - Risk: Services competing for resources
   - Need: Service-level resource quotas

3. **Mode Synchronization**
   - Risk: Inconsistent states
   - Need: Mode transition orchestration

## 6. Implementation Recommendations

### 1. Phased Rollout
1. Update directory structure
2. Implement org-level config
3. Add multi-service support
4. Enhance monitoring
5. Package Golden Goose v1
6. Enable compliance mode

### 2. Required Guardrails
- Service health checks must pass before mode switch
- Automated dependency validation
- Resource limit enforcement per service
- Cross-service monitoring

### 3. Configuration Management
```yaml
org:
  default_mode: sandbox
  resource_limits:
    sandbox:
      cpu: "0.1-0.5"
      memory: "128-512Mi"
    compliance:
      cpu: "0.1-16.0"
      memory: "128-32768Mi"
  
services:
  override_allowed: false
  mode_switch:
    requires_approval: true
    auto_switch: false
```

## 7. Questions for CTO

1. **Directory Structure**
   - Confirm proposed hierarchical structure
   - Clarify report retention per service

2. **Mode Management**
   - Confirm if services can be in different modes
   - Define mode switch prerequisites

3. **Resource Management**
   - Confirm if resources are allocated per service
   - Define resource sharing policies

4. **Monitoring**
   - Specify alert thresholds
   - Confirm metric retention periods

5. **Golden Goose Packaging**
   - Confirm versioning strategy
   - Define release criteria

---
Generated: September 24, 2025
Repository: Fintech-Blueprint/example-service
Branch: auto/spec-implementation/445771e99fbb