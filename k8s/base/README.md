# Kubernetes Base Manifests

This directory contains base Kubernetes manifests for the PubSec Info Assistant system.

## Structure

- `backend-deployment.yaml` - Backend API deployment
- `frontend-deployment.yaml` - Frontend React app deployment
- `qdrant-statefulset.yaml` - Qdrant vector database
- `redis-statefulset.yaml` - Redis cache
- `services.yaml` - All service definitions
- `configmaps.yaml` - Configuration data
- `secrets.yaml.example` - Secret templates (DO NOT commit actual secrets)
- `ingress.yaml` - Ingress configuration
- `hpa.yaml` - Horizontal Pod Autoscalers
- `pdb.yaml` - Pod Disruption Budgets
- `network-policy.yaml` - Network policies for tenant isolation
- `kustomization.yaml` - Kustomize configuration

## Usage

### With kubectl:
```bash
kubectl apply -k k8s/base
```

### With Kustomize overlays:
```bash
# Development
kubectl apply -k k8s/overlays/dev

# Staging
kubectl apply -k k8s/overlays/staging

# Production
kubectl apply -k k8s/overlays/production
```

## Secrets

Copy `secrets.yaml.example` to `secrets.yaml` and fill in actual values:
```bash
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with actual credentials
kubectl apply -f secrets.yaml
```

Remember to NEVER commit `secrets.yaml` to version control.
