# New Codespace Setup Guide

This guide documents the exact steps needed to set up a new codespace for working with this repository and Vault. These steps have been validated and represent the minimal successful path.

## Quick Start (TL;DR)

```bash
# 1. GitHub Setup
unset GITHUB_TOKEN
gh auth login -h github.com -p https -s "workflow,repo,admin:org" -w

# 2. Install Vault
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install -y vault

# 3. Configure Vault
export VAULT_ADDR="https://vault-cluster-public-vault-d81cdec2.2d1e9c46.z1.hashicorp.cloud:8200"
export VAULT_NAMESPACE="admin"
export VAULT_TOKEN="<paste-your-new-admin-token-here>"
vault status
```

## Detailed Setup Instructions

## 1. GitHub Authentication Setup

First, clear any existing GitHub token and authenticate with GitHub CLI:

```bash
# Clear any existing GitHub token that might interfere with authentication
unset GITHUB_TOKEN

# Authenticate with GitHub CLI (this will open a browser window)
gh auth login -h github.com -p https -s "workflow,repo,admin:org" -w

# After running this command:
# 1. Copy the one-time code shown in the terminal
# 2. Press Enter to open the browser
# 3. Paste the code in GitHub's device activation page
# 4. Authorize the device
```

## 2. Vault Setup

### Install Vault CLI

```bash
# Add HashiCorp GPG key and repository
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Install Vault
sudo apt-get update && sudo apt-get install -y vault
```

### Configure Vault Environment

1. Go to [HashiCorp Cloud Platform Vault](https://portal.cloud.hashicorp.com/services/vault/vault-cluster?project_id=2548fc76-693d-4284-b738-bb8a320bf734)
2. Generate a new admin token
3. Set up your environment with the new token:

```bash
# Set Vault address and namespace
export VAULT_ADDR="https://vault-cluster-public-vault-d81cdec2.2d1e9c46.z1.hashicorp.cloud:8200"
export VAULT_NAMESPACE="admin"

# Set your newly generated admin token
export VAULT_TOKEN="<paste-your-new-admin-token-here>"

# Verify Vault connection
vault status
```

## 3. Verify Configuration

After setting up, verify that everything is working:

```bash
# Verify GitHub CLI authentication
gh auth status

# Verify Vault connectivity and permissions
vault auth list
```

## Notes

- Each new codespace requires these setup steps as environment variables don't persist between sessions
- Generate a new admin token from the HashiCorp Cloud Portal for each new session
- The GitHub authentication only needs to be done once per codespace
- Never commit tokens or sensitive credentials to the repository

## Troubleshooting

### Common Issues We've Encountered

1. GitHub Authentication Issues
   - **Symptom**: "GITHUB_TOKEN environment variable is being used for authentication"
   - **Solution**: Run `unset GITHUB_TOKEN` first, then retry authentication
   - **Why**: The presence of GITHUB_TOKEN prevents local device authentication

2. Vault Permission Issues
   - **Symptom**: "permission denied" or Error 403 in Vault commands
   - **Root Cause**: Token not set or insufficient privileges
   - **Solutions**:
     ```bash
     # Verify token is set
     echo $VAULT_TOKEN
     
     # Verify token has correct permissions
     vault token lookup
     
     # Generate new token if needed from HCP portal
     ```

3. HashiCorp Repository Setup
   - **Symptom**: "Unable to locate package vault" or GPG errors
   - **Solutions**:
     ```bash
     # Verify Ubuntu version
     lsb_release -cs
     
     # Manually add repository if auto-detection fails
     sudo add-apt-repository "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
     ```

4. Network Connectivity
   - **Symptom**: "connection refused" or timeout errors
   - **Solution**: Verify Vault address and network access
     ```bash
     # Test Vault connectivity
     curl -k $VAULT_ADDR/v1/sys/health
     ```

### Environment Verification

Run this health check to verify your setup:
```bash
# Check all components
gh auth status
vault status
vault token lookup | grep policies
```

Expected output should show:
- GitHub: Logged in
- Vault: Unsealed, active
- Token: Required policies present

## Security Reminders

### Token Management
- Always revoke admin tokens after your session
  ```bash
  # Revoke current token
  vault token revoke -self
  ```
- Use time-limited tokens when possible
  - In HCP Portal, set token TTL to match your work session
  - Consider using periodic tokens for longer sessions

### Environment Security
- Keep the portal URL and any credentials secure
- Never share or commit tokens to version control
- Clear sensitive environment variables when done:
  ```bash
  unset VAULT_TOKEN
  unset GITHUB_TOKEN
  ```

### Best Practices
- Create a new admin token for each work session
- Don't reuse tokens between codespaces
- Monitor token usage in HCP Vault audit logs
- Use separate tokens for development and CI/CD

### Emergency Steps
If you suspect a token has been compromised:
1. Revoke the token immediately in HCP Portal
2. Check the audit logs for unauthorized access
3. Rotate any exposed secrets
4. Report the incident to security team