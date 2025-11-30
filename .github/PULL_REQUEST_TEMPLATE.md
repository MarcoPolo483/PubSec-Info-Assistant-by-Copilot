## Description
<!-- Provide a brief description of the changes in this PR -->

## Related Issue
<!-- Link to the issue this PR addresses -->
Closes #<!-- issue number -->

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)
- [ ] CI/CD improvement
- [ ] Security improvement

## Checklist

### Code Quality
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings

### Testing
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Test coverage is maintained at ≥80%
- [ ] Integration tests pass (if applicable)
- [ ] E2E tests pass for critical flows (if applicable)

### Multi-Tenancy (if applicable)
- [ ] Tenant isolation validated (no data leakage between tenants)
- [ ] Cross-tenant authorization tests added
- [ ] Rate limiting tested per tenant
- [ ] Cost tracking validated

### Security
- [ ] Security considerations documented
- [ ] No secrets committed (API keys, passwords, certificates)
- [ ] Input validation implemented
- [ ] Output encoding applied
- [ ] OWASP Top 10 mitigations considered
- [ ] Security scan passed (Snyk, Trivy, OWASP ZAP)

### Performance
- [ ] Performance impact assessed
- [ ] No performance degradation introduced
- [ ] Load testing performed (if applicable)
- [ ] Caching strategy optimized (if applicable)

### Accessibility
- [ ] WCAG 2.1 AA compliance maintained (if frontend changes)
- [ ] Keyboard navigation tested
- [ ] Screen reader compatibility verified
- [ ] Color contrast ratios checked (minimum 4.5:1)

### Documentation
- [ ] I have updated the README (if needed)
- [ ] I have updated API documentation (if API changes)
- [ ] I have added/updated runbooks (if operational changes)
- [ ] I have added/updated architecture docs (if architectural changes)
- [ ] Migration notes added (if breaking changes)

### Deployment
- [ ] Docker images build successfully
- [ ] K8s manifests validated
- [ ] Terraform configurations validated (if infra changes)
- [ ] Environment variables documented (if new configs)
- [ ] Backward compatibility maintained (or migration path provided)

### Cost Impact
- [ ] Cost impact analyzed (LLM tokens, compute, storage)
- [ ] Cost optimization considered
- [ ] Per-tenant cost tracked (if applicable)

## Screenshots (if applicable)
<!-- Add screenshots to demonstrate UI changes -->

## Testing Evidence
<!-- Describe the testing you performed -->

### Unit Tests
```
# Paste test results showing coverage
```

### Integration Tests
```
# Paste integration test results
```

### Performance Tests
```
# Paste performance test results (latency, throughput)
```

## Migration Notes (if applicable)
<!-- Describe any migration steps required for deployment -->

## Rollback Plan
<!-- Describe how to rollback this change if issues arise in production -->

## Additional Notes
<!-- Any additional information reviewers should know -->

## Review Checklist for Maintainers
- [ ] Code follows project conventions
- [ ] Tests are comprehensive and pass
- [ ] Documentation is complete and accurate
- [ ] Security implications assessed
- [ ] Performance impact acceptable
- [ ] No breaking changes (or migration path provided)
- [ ] Multi-tenancy isolation maintained (if applicable)
- [ ] CI/CD pipeline passes
