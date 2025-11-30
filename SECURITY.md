# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please follow responsible disclosure practices:

### How to Report

1. **Email**: Send details to marco.polo483@protonmail.com
2. **Subject Line**: "Security Vulnerability - PubSec Info Assistant"
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)
   - Your contact information

### What to Expect

* **Initial Response**: Within 24 hours
* **Status Update**: Within 72 hours
* **Triage**: We will investigate and confirm the vulnerability
* **Fix Timeline**:
  - CRITICAL: 7 days
  - HIGH: 30 days
  - MEDIUM: 90 days
  - LOW: Best effort

### Disclosure Policy

* We request that you do not publicly disclose the vulnerability until we have released a fix
* We will acknowledge your contribution in the security advisory (unless you prefer to remain anonymous)
* We will keep you informed of our progress

### Bug Bounty Program

We currently do not offer a paid bug bounty program, but we deeply appreciate security researchers' efforts and will:

* Publicly acknowledge your contribution (if desired)
* List you in our Hall of Fame
* Provide swag/merchandise (for significant findings)

## Security Best Practices

### For Developers

1. **Never commit secrets**:
   - Use environment variables
   - Use secret management services (Azure Key Vault, AWS Secrets Manager)
   - Enable secret scanning

2. **Dependency Management**:
   - Keep dependencies up to date
   - Run `npm audit` and `pip-audit` regularly
   - Enable Dependabot alerts

3. **Code Review**:
   - All code must be reviewed by at least 2 maintainers
   - Security-sensitive code requires additional review
   - Run SAST tools (SonarQube, Semgrep)

4. **Testing**:
   - Include security tests in CI/CD
   - Run OWASP ZAP scans
   - Perform penetration testing annually

### For Users/Deployers

1. **Authentication**:
   - Enable MFA for all admin accounts
   - Rotate API keys every 90 days
   - Use strong passwords (minimum 16 characters)

2. **Network Security**:
   - Deploy behind a firewall
   - Use TLS 1.3 for all connections
   - Implement IP whitelisting for admin access

3. **Data Protection**:
   - Enable encryption at rest (AES-256)
   - Enable encryption in transit (TLS 1.3)
   - Implement PII redaction

4. **Monitoring**:
   - Enable audit logging
   - Set up security alerts
   - Monitor for suspicious activity

5. **Updates**:
   - Apply security patches within 7 days
   - Subscribe to security advisories
   - Test updates in staging first

## Known Security Considerations

### Multi-Tenancy

* **Data Isolation**: Tenant data is isolated at the vector index level
* **Resource Isolation**: Separate pods/containers per tenant tier
* **Network Isolation**: VPC/subnet per enterprise tenant (optional)
* **Cross-Tenant Protection**: All queries validate tenant_id, test suite includes data leakage tests

### API Security

* **Authentication**: OAuth2 + JWT with RS256 signing
* **Rate Limiting**: Token bucket algorithm, per-tenant quotas
* **Input Validation**: Whitelist validation, max length checks
* **Output Encoding**: Context-aware encoding (HTML, JSON, SQL)

### LLM Security

* **Prompt Injection**: Input sanitization, system prompts protected
* **Content Filtering**: Azure OpenAI content filters (violence, hate, sexual, self-harm)
* **Hallucination Detection**: Automated fact-checking against source documents
* **PII Protection**: Automated PII redaction using NER models

### Infrastructure Security

* **Container Security**: Distroless images, vulnerability scanning (Trivy)
* **Pod Security**: Restricted PSS (no privileged, read-only root FS)
* **Network Policies**: Default deny-all, explicit allow rules
* **Secrets Management**: Sealed secrets or external secrets operator

## Compliance

This project is designed to meet:

* **SOC2 Type II**: Security, Availability, Confidentiality
* **FedRAMP Moderate**: NIST 800-53 controls
* **GDPR**: Data protection and privacy
* **WCAG 2.1 Level AA**: Accessibility

See [docs/compliance.md](docs/compliance.md) for detailed control mappings.

## Security Contacts

* **Primary**: marco.polo483@protonmail.com
* **Security Advisories**: https://github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot/security/advisories

## Hall of Fame

We thank the following security researchers for responsibly disclosing vulnerabilities:

*(No reports yet - be the first!)*

---

**Last Updated**: November 30, 2025
