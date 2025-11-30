# Migration Plan: EVA Domain Assistant 2.0 Repository Cleansing

**Date**: November 30, 2025  
**Purpose**: Prepare PubSec-Info-Assistant-by-Copilot for migration to eva-da-2 repository  
**Target**: EVA Domain Assistant 2.0 (EVA-DA-2) - Second product in EVA Suite family

---

## Executive Summary

This repository will become **EVA Domain Assistant 2.0 (EVA-DA-2)**, the second product in the EVA Suite family (first being EVA Sovereign UI). Complete cleansing required to remove all references to:
- Copilot/Spark development origins
- Temporary branch names (merge-spark-copilot)
- Old repository URLs (PubSec-Info-Assistant-by-Copilot)
- Development artifacts and leftover naming

**New Identity**:
- **Product Name**: EVA Domain Assistant 2.0
- **Short Name**: EVA-DA-2
- **Repository**: eva-da-2
- **GitHub URL**: https://github.com/EVA-Suite/eva-da-2
- **Description**: Enterprise-grade domain-specific AI assistant with RAG capabilities, leveraging EVA Sovereign UI components

---

## Impact Analysis

### 1. Repository Name Change

**Current**: `PubSec-Info-Assistant-by-Copilot`  
**New**: `eva-da-2`

**Impact**:
- ✅ **Low Risk** - Git history preserved during repository rename
- ✅ **GitHub redirects** - Old URLs automatically redirect for 6+ months
- ⚠️ **CI/CD pipelines** - Need to update GitHub Actions workflows
- ⚠️ **Documentation** - 50+ files with hardcoded repository URLs
- ⚠️ **Docker images** - Container registry paths need updating

### 2. Product Branding

**Changes Required**:
- All "PubSec Info Assistant" → "EVA Domain Assistant 2.0"
- All "Info Assistant" → "EVA-DA-2" or "Domain Assistant"
- All "by-Copilot" references → Remove completely
- All "by Copilot" references → Remove completely

### 3. Branch Name Cleanup

**Remove all references to**:
- `merge-spark-copilot` (temporary merge branch)
- `spark` (development tool reference)
- Old feature branches

### 4. GitHub URLs and References

**Update Pattern**:
```
OLD: github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot
NEW: github.com/EVA-Suite/eva-da-2
```

**Affected Files** (Estimated 50+ files):
- All Markdown documentation (*.md)
- GitHub workflows (.github/workflows/*.yml)
- Kubernetes manifests (k8s/**/*.yaml)
- Terraform configurations (terraform/**/*.tf)
- Docker Compose files
- Package manifests (package.json if any)
- CI/CD configuration

---

## Files Requiring Updates

### High Priority (Must Change)

#### 1. Core Documentation
- [ ] `README.md` - Main project description
- [ ] `PROJECT-SUMMARY.md` - Project overview
- [ ] `DEPLOYMENT-OPTIONS.md` - Deployment instructions
- [ ] `DEPLOYMENT-READINESS.md` - Readiness certification
- [ ] `INTERNATIONAL-DEPLOYMENT-GUIDE.md` - International guide
- [ ] `DEMO-GUIDE.md` - Demo instructions
- [ ] `SECURITY.md` - Security policies
- [ ] `CONTRIBUTING.md` - Contribution guidelines
- [ ] `CODE_OF_CONDUCT.md` - Community standards

#### 2. Deployment Configuration
- [ ] `docker-compose.yml` - Container orchestration
- [ ] `k8s/base/kustomization.yaml` - Kubernetes base config
- [ ] `k8s/base/backend-deployment.yaml` - Backend deployment
- [ ] `k8s/base/frontend-deployment.yaml` - Frontend deployment
- [ ] All `k8s/overlays/**/*.yaml` - Environment overlays

#### 3. CI/CD Pipelines
- [ ] `.github/workflows/ci.yml` - Continuous integration
- [ ] `.github/workflows/cd.yml` - Continuous deployment
- [ ] `.github/workflows/security.yml` - Security scanning
- [ ] `.github/workflows/performance.yml` - Performance testing

#### 4. Terraform Infrastructure
- [ ] `terraform/TSHIRT-SIZING-GUIDE.md` - Sizing documentation
- [ ] `terraform/README.md` - Terraform overview
- [ ] All `terraform/**/*.tf` - Infrastructure code

#### 5. Compliance Documentation
- [ ] `docs/compliance/SOC2-COMPLIANCE.md`
- [ ] All compliance and audit documents

### Medium Priority (Should Change)

#### 6. Development Artifacts
- [ ] Test files with hardcoded paths
- [ ] Coverage reports with old paths
- [ ] Build scripts
- [ ] Local development configs

### Low Priority (Nice to Have)

#### 7. Git History References
- [ ] Git commit messages (informational only - cannot change)
- [ ] Old branch references in documentation

---

## Detailed File Changes

### Pattern 1: Repository URLs

**Find & Replace**:
```
Find:    https://github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot
Replace: https://github.com/EVA-Suite/eva-da-2

Find:    github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot
Replace: github.com/EVA-Suite/eva-da-2

Find:    MarcoPolo483/PubSec-Info-Assistant-by-Copilot
Replace: EVA-Suite/eva-da-2
```

### Pattern 2: Directory Names

**Find & Replace**:
```
Find:    PubSec-Info-Assistant-by-Copilot
Replace: eva-da-2

Find:    cd PubSec-Info-Assistant-by-Copilot
Replace: cd eva-da-2
```

### Pattern 3: Product Names

**Find & Replace**:
```
Find:    PubSec Info Assistant
Replace: EVA Domain Assistant 2.0

Find:    Info Assistant
Replace: EVA Domain Assistant 2.0

Find:    PubSec Information Assistant
Replace: EVA Domain Assistant 2.0
```

### Pattern 4: Container Images

**Find & Replace**:
```
Find:    ghcr.io/marcopolo483/pubsec-info-assistant-by-copilot
Replace: ghcr.io/eva-suite/eva-da-2

Find:    pubsec-info-assistant-by-copilot
Replace: eva-da-2
```

### Pattern 5: Branch References

**Find & Replace**:
```
Find:    merge-spark-copilot
Replace: main

Find:    @merge-spark-copilot
Replace: @main

Find:    origin/merge-spark-copilot
Replace: origin/main
```

### Pattern 6: Copilot/Spark References

**Find & Replace**:
```
Find:    by-Copilot
Replace: (remove completely)

Find:    by Copilot
Replace: (remove completely)

Find:    GitHub Copilot Agent
Replace: EVA Development Team

Find:    Built by GitHub Copilot
Replace: Built by EVA Suite Team

Find:    spark-copilot
Replace: (remove completely)
```

---

## Metadata Updates

### GitHub Repository Settings

**After repository rename**:
1. **Repository Name**: eva-da-2
2. **Description**: "EVA Domain Assistant 2.0 - Enterprise RAG-based AI assistant leveraging EVA Sovereign UI"
3. **Topics/Tags**:
   - eva-suite
   - domain-assistant
   - rag
   - azure
   - kubernetes
   - enterprise-ai
   - government-cloud
   - wcag
   - fedramp

4. **Homepage URL**: https://eva-suite.github.io/eva-da-2
5. **About**:
   ```
   EVA Domain Assistant 2.0: Enterprise-grade domain-specific AI assistant with 
   Retrieval-Augmented Generation (RAG) capabilities. Built on EVA Sovereign UI 
   components for world-class accessibility and government compliance (FedRAMP, 
   WCAG 2.2 AA+, SOC 2).
   ```

### Package Manifests (if applicable)

**package.json** (if exists):
```json
{
  "name": "@eva-suite/eva-da-2",
  "version": "2.0.0",
  "description": "EVA Domain Assistant 2.0 - Enterprise RAG-based AI assistant",
  "repository": {
    "type": "git",
    "url": "https://github.com/EVA-Suite/eva-da-2.git"
  },
  "bugs": {
    "url": "https://github.com/EVA-Suite/eva-da-2/issues"
  },
  "homepage": "https://github.com/EVA-Suite/eva-da-2#readme"
}
```

### Docker Labels

**Dockerfile.backend** and **Dockerfile.frontend**:
```dockerfile
LABEL org.opencontainers.image.title="EVA Domain Assistant 2.0 - Backend"
LABEL org.opencontainers.image.description="Enterprise RAG backend for EVA-DA-2"
LABEL org.opencontainers.image.url="https://github.com/EVA-Suite/eva-da-2"
LABEL org.opencontainers.image.source="https://github.com/EVA-Suite/eva-da-2"
LABEL org.opencontainers.image.vendor="EVA Suite"
```

---

## Execution Plan

### Phase 1: Preparation (Pre-Migration)
**Duration**: 1-2 hours

1. **Create backup branch**
   ```bash
   git checkout -b pre-eva-da-2-migration
   git push origin pre-eva-da-2-migration
   ```

2. **Generate file list for changes**
   ```bash
   cd "c:\Users\marco\Documents\_AI Dev\EVA Suite\PubSec-Info-Assistant-by-Copilot"
   
   # Find all files with old references
   git grep -l "PubSec-Info-Assistant-by-Copilot" > files-to-update.txt
   git grep -l "merge-spark-copilot" >> files-to-update.txt
   git grep -l "by-Copilot" >> files-to-update.txt
   sort -u files-to-update.txt -o files-to-update.txt
   ```

3. **Review all files**
   - Manual review of critical files
   - Identify any edge cases
   - Plan custom replacements

### Phase 2: Automated Cleanup
**Duration**: 30 minutes

Execute PowerShell script to perform bulk find-replace across all files:

```powershell
# See MIGRATION-CLEANUP-SCRIPT.ps1
```

### Phase 3: Manual Verification
**Duration**: 1 hour

1. Review changed files manually
2. Test build process
3. Verify documentation renders correctly
4. Check all links

### Phase 4: Repository Migration
**Duration**: 30 minutes

1. **GitHub Repository Rename**
   - Settings → General → Repository name → "eva-da-2"
   - Confirm rename

2. **Update local Git configuration**
   ```bash
   git remote set-url origin https://github.com/EVA-Suite/eva-da-2.git
   ```

3. **Push cleaned changes**
   ```bash
   git add .
   git commit -m "refactor: rebrand as EVA Domain Assistant 2.0

Complete rebranding from PubSec-Info-Assistant-by-Copilot to EVA-DA-2:
- Remove all Copilot/Spark development references
- Update repository URLs to eva-suite/eva-da-2
- Rebrand as EVA Domain Assistant 2.0
- Clean up temporary branch references (merge-spark-copilot)
- Update container registry paths
- Refresh all documentation
- Align with EVA Suite product family

This is the second product in the EVA Suite family (after EVA Sovereign UI).
EVA-DA-2 leverages EVA Sovereign UI components for enterprise-grade
accessibility and government compliance."
   
   git push origin main
   ```

### Phase 5: Post-Migration Verification
**Duration**: 1 hour

1. **Test CI/CD pipelines**
   - Trigger GitHub Actions
   - Verify builds succeed
   - Check deployment workflows

2. **Update external references**
   - Docker Hub / GitHub Container Registry
   - Documentation sites
   - Wiki pages (if any)

3. **Update README badges**
   - CI status badges
   - Coverage badges
   - Version badges

4. **Notify stakeholders**
   - Send migration announcement
   - Update team documentation
   - Update project management systems

---

## Risk Mitigation

### Rollback Plan

If issues occur:
1. **Repository name**: Can rename back within 90 days
2. **Code changes**: Revert to `pre-eva-da-2-migration` branch
3. **Container images**: Keep old registry paths for 6 months

### Testing Checklist

Before finalizing:
- [ ] All GitHub Actions pass
- [ ] Docker images build successfully
- [ ] Documentation renders without broken links
- [ ] Terraform plans execute without errors
- [ ] Kubernetes manifests validate
- [ ] Local development workflow works
- [ ] Demo guide commands are accurate

---

## Post-Migration Tasks

### Documentation Updates

1. **Create EVA-DA-2 landing page**
2. **Update EVA Suite family documentation**
3. **Create migration guide for users**
4. **Update product comparison matrix**

### Integration with EVA Sovereign UI

Document how EVA-DA-2 leverages EVA Sovereign UI:
- Component library usage
- Theming integration
- Accessibility features
- Design system compliance

### Deprecation Notice (Old Repository)

If keeping old repository for redirect:
```markdown
# ⚠️ Repository Moved

This repository has been migrated to:
**https://github.com/EVA-Suite/eva-da-2**

PubSec Info Assistant is now **EVA Domain Assistant 2.0**,
the second product in the EVA Suite family.

All new development, issues, and discussions should be
directed to the new repository.

This repository will remain for historical purposes and
will redirect to the new location.
```

---

## Success Criteria

✅ **Complete** when:
1. Zero references to "by-Copilot" or "by Copilot"
2. Zero references to "merge-spark-copilot" branch
3. All GitHub URLs point to eva-suite/eva-da-2
4. All documentation uses "EVA Domain Assistant 2.0" or "EVA-DA-2"
5. CI/CD pipelines pass
6. Docker images build and push successfully
7. All links in documentation are valid
8. Terraform configurations validate
9. Demo guide is accurate and tested

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Preparation | 1-2 hours | Not Started |
| Automated Cleanup | 30 minutes | Not Started |
| Manual Verification | 1 hour | Not Started |
| Repository Migration | 30 minutes | Not Started |
| Post-Migration | 1 hour | Not Started |
| **Total** | **4-5 hours** | |

---

## Next Steps

1. **Review this plan** - Confirm approach with stakeholders
2. **Schedule migration window** - Choose low-traffic time
3. **Execute preparation phase** - Create backup and file lists
4. **Run automated cleanup** - Execute PowerShell script
5. **Verify changes** - Manual review and testing
6. **Perform migration** - Repository rename and push
7. **Validate** - Run all tests and checks
8. **Announce** - Communicate to team and users

---

**Prepared By**: GitHub Copilot Agent  
**Last Updated**: November 30, 2025  
**Status**: Ready for execution
