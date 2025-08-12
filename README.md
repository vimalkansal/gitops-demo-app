# GitOps Demo Application with DORA Metrics

This repository demonstrates a complete GitOps pipeline with DORA metrics collection using Red Hat OpenShift, ArgoCD (Red Hat GitOps), and Pelorus.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup Instructions](#detailed-setup-instructions)
- [DORA Metrics Configuration](#dora-metrics-configuration)
- [Monitoring and Dashboards](#monitoring-and-dashboards)
- [Troubleshooting](#troubleshooting)
- [CI/CD Pipeline](#cicd-pipeline)

## Architecture Overview

```
GitHub Repository → GitHub Actions → Container Registry (GHCR)
                          ↓
                    ArgoCD (GitOps)
                          ↓
                 OpenShift Cluster
                          ↓
                  Pelorus (DORA Metrics)
                          ↓
                  Grafana Dashboards
```

### Components:
- **Application**: Simple Python Flask app demonstrating GitOps deployment
- **CI/CD**: GitHub Actions for building and pushing container images
- **GitOps**: ArgoCD automatically syncs Kubernetes manifests from Git
- **Metrics**: Pelorus collects DORA metrics (Deployment Frequency, Lead Time, MTTR, Change Failure Rate)
- **Visualization**: Grafana dashboards display DORA metrics

## Prerequisites

### Required Components
1. **OpenShift Cluster** (v4.10+)
   - Access to create projects/namespaces
   - Ability to install operators

2. **Red Hat GitOps Operator** (ArgoCD)
   ```bash
   # Verify GitOps is installed
   oc get operators -n openshift-operators | grep gitops
   ```

3. **Pelorus** installed in `pelorus` namespace
   ```bash
   # Verify Pelorus is installed
   oc get pelorus -n pelorus
   ```

4. **GitHub Account** with:
   - Fork of this repository
   - GitHub Actions enabled
   - Container registry access (ghcr.io)

### Required CLI Tools
- `oc` (OpenShift CLI)
- `git`
- `kubectl` (optional, for local testing)

## Quick Start

1. **Fork and Clone Repository**
   ```bash
   # Fork this repo in GitHub UI first, then:
   git clone https://github.com/<your-username>/gitops-demo-app.git
   cd gitops-demo-app
   ```

2. **Login to OpenShift**
   ```bash
   oc login <your-cluster-url>
   ```

3. **Deploy ArgoCD Application**
   ```bash
   # Update the repository URL in argocd/application.yaml to point to your fork
   sed -i "s|vimalkansal|<your-github-username>|g" argocd/application.yaml
   
   # Apply the ArgoCD application
   oc apply -f argocd/application.yaml
   ```

4. **Configure Pelorus for Your Namespace**
   ```bash
   # Add pelorus-demo namespace to Pelorus monitoring
   oc patch pelorus pelorus-quickstart -n pelorus --type='json' \
     -p='[{"op": "replace", "path": "/spec/exporters/instances/0/extraEnv/0/value", "value": "pelorus-demo"}]'
   ```

5. **Access the Application**
   ```bash
   # Get the application URL
   oc get route demo-app -n pelorus-demo -o jsonpath='https://{.spec.host}{"\n"}'
   ```

## Detailed Setup Instructions

### Step 1: Fork and Configure Repository

1. Fork this repository to your GitHub account
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/gitops-demo-app.git
   cd gitops-demo-app
   ```

3. Update repository references:
   ```bash
   # Update ArgoCD application to point to your fork
   sed -i "s|https://github.com/vimalkansal/gitops-demo-app|https://github.com/<your-username>/gitops-demo-app|g" argocd/application.yaml
   
   # Update image references in kustomization
   sed -i "s|ghcr.io/vimalkansal/gitops-demo-app|ghcr.io/<your-username>/gitops-demo-app|g" k8s/overlays/prod/kustomization.yaml
   
   # Commit changes
   git add -A
   git commit -m "Update repository references"
   git push
   ```

### Step 2: Deploy ArgoCD Application

1. Ensure you're logged into OpenShift:
   ```bash
   oc login <cluster-url>
   ```

2. Create the ArgoCD application:
   ```bash
   oc apply -f argocd/application.yaml
   ```

3. Verify application creation:
   ```bash
   oc get application demo-app -n openshift-gitops
   ```

4. Check sync status:
   ```bash
   oc get application demo-app -n openshift-gitops -o jsonpath='Sync: {.status.sync.status}, Health: {.status.health.status}{"\n"}'
   ```

### Step 3: Configure Pelorus for DORA Metrics

1. **Get current Pelorus configuration:**
   ```bash
   oc get pelorus -n pelorus -o yaml | grep -A 10 "exporters:"
   ```

2. **Update Pelorus to monitor your namespace:**
   ```bash
   # Get the Pelorus instance name
   PELORUS_INSTANCE=$(oc get pelorus -n pelorus -o jsonpath='{.items[0].metadata.name}')
   
   # Update the namespace list (add pelorus-demo to existing namespaces)
   oc patch pelorus $PELORUS_INSTANCE -n pelorus --type='json' \
     -p='[{"op": "replace", "path": "/spec/exporters/instances/0/extraEnv/0/value", "value": "pelorus-demo"}]'
   ```

3. **Restart Pelorus exporters to pick up changes:**
   ```bash
   # Delete exporter pods to force restart
   oc delete pods -n pelorus -l app.kubernetes.io/name=deploytime-exporter
   oc delete pods -n pelorus -l app.kubernetes.io/name=committime-exporter
   ```

4. **Verify exporters are monitoring your namespace:**
   ```bash
   # Check deploytime exporter logs
   oc logs -n pelorus -l app.kubernetes.io/name=deploytime-exporter | grep pelorus-demo
   ```

### Step 4: Verify Deployment

1. **Check if application is deployed:**
   ```bash
   oc get all -n pelorus-demo
   ```

2. **Access the application:**
   ```bash
   # Get route URL
   APP_URL=$(oc get route demo-app -n pelorus-demo -o jsonpath='https://{.spec.host}')
   echo "Application URL: $APP_URL"
   
   # Test the application
   curl -k $APP_URL
   ```

3. **Verify Pelorus annotations:**
   ```bash
   # Check deployment annotations
   oc get deployment demo-app -n pelorus-demo -o jsonpath='{.metadata.annotations}' | jq '.'
   
   # Check pod annotations
   oc get pod -n pelorus-demo -l app.kubernetes.io/name=demo-app -o jsonpath='{.items[0].metadata.annotations}' | jq '.'
   ```

## DORA Metrics Configuration

### Understanding DORA Metrics

1. **Deployment Frequency**: How often you deploy to production
2. **Lead Time for Changes**: Time from code commit to production
3. **Mean Time to Restore (MTTR)**: Time to recover from failures
4. **Change Failure Rate**: Percentage of deployments causing failures

### Required Annotations for Metrics

The following annotations are automatically set by the CI/CD pipeline:

```yaml
metadata:
  annotations:
    # For Lead Time calculation
    app.kubernetes.io/vcs-ref: "<git-commit-sha>"
    app.kubernetes.io/vcs-uri: "https://github.com/<user>/gitops-demo-app"
    
    # For Deployment Frequency
    deploy-time: "<ISO-8601-timestamp>"
    
    # For build tracking
    app.kubernetes.io/build-id: "<build-number>"
    app.kubernetes.io/build-url: "<github-actions-url>"
    
    # For Change tracking
    app.kubernetes.io/change-id: "<pr-number-or-commit>"
    app.kubernetes.io/approved-by: "github-actions"
    app.kubernetes.io/approved-at: "<approval-timestamp>"
```

### Enabling All DORA Metrics

#### 1. Lead Time for Changes (Commit to Deploy Time)

To enable Lead Time metrics, configure the committime exporter with GitHub access:

```bash
# 1. Create GitHub Personal Access Token
# Go to GitHub Settings → Developer Settings → Personal Access Tokens
# Create token with 'repo' scope for private repos or 'public_repo' for public

# 2. Create secret with your GitHub token
oc create secret generic github-credentials \
  --from-literal=github_token=YOUR_GITHUB_TOKEN \
  -n pelorus

# 3. Apply committime exporter configuration
oc apply -f pelorus/configure-committime-exporter.yaml

# 4. Verify committime exporter is running
oc get pods -n pelorus -l app.kubernetes.io/name=committime-exporter

# 5. Check metrics are being collected
oc exec -n pelorus $(oc get pod -n pelorus -l app.kubernetes.io/name=committime-exporter -o name | head -1) -- \
  curl -s localhost:8080/metrics | grep commit_timestamp
```

#### 2. Deployment Frequency

Automatically tracked when deployments occur. Already configured through:
- Deployment annotations with timestamps
- Deploytime exporter monitoring the namespace

Verify it's working:
```bash
# Check deployment metrics
oc exec -n pelorus $(oc get pod -n pelorus -l app.kubernetes.io/name=deploytime-exporter -o name | head -1) -- \
  curl -s localhost:8080/metrics | grep deploy_timestamp
```

#### 3. Mean Time to Restore (MTTR)

MTTR requires incident/failure tracking. This demo includes example configurations:

**Option A: Manual Incident Tracking (for testing)**
```bash
# Apply example failure data
oc apply -f pelorus/failure-data-configmap.yaml

# Configure failure exporter to use the data
oc set env dc/failure-exporter -n pelorus \
  FAILURE_DATA_SOURCE=configmap \
  FAILURE_CONFIGMAP=demo-app-failure-data
```

**Option B: Automated Incident Tracking (production)**

For production, integrate with your incident management system:

```bash
# For ServiceNow integration
oc create secret generic servicenow-credentials \
  --from-literal=username=YOUR_USERNAME \
  --from-literal=password=YOUR_PASSWORD \
  --from-literal=instance=YOUR_INSTANCE.service-now.com \
  -n pelorus

# Configure failure exporter for ServiceNow
oc set env dc/failure-exporter -n pelorus \
  FAILURE_DATA_SOURCE=servicenow \
  SERVICENOW_USERNAME=YOUR_USERNAME \
  SERVICENOW_INSTANCE=YOUR_INSTANCE.service-now.com
```

#### 4. Change Failure Rate

Change Failure Rate is tracked through test results and deployment outcomes. This repo includes:

**Automated Test Integration:**
- GitHub Actions workflow (`test-and-deploy.yml`) runs tests
- Test results are added as annotations on deployments
- Pelorus tracks success/failure rates

To enable:
```bash
# 1. Switch to the test-and-deploy workflow
mv .github/workflows/cicd.yml .github/workflows/cicd.yml.bak
mv .github/workflows/test-and-deploy.yml .github/workflows/cicd.yml

# 2. Commit and push to trigger the new workflow
git add .github/workflows/
git commit -m "Enable test tracking for Change Failure Rate"
git push

# 3. Monitor test results in annotations
oc get deployment demo-app -n pelorus-demo -o jsonpath='{.metadata.annotations}' | jq '.' | grep test
```

**Manual Rollback Tracking:**
```bash
# When a deployment fails and needs rollback
oc annotate deployment demo-app -n pelorus-demo \
  app.kubernetes.io/rollback="true" \
  app.kubernetes.io/rollback-reason="Performance degradation" \
  --overwrite
```

## Monitoring and Dashboards

### Accessing Grafana

1. **Get Grafana URL:**
   ```bash
   oc get route -n pelorus grafana-route -o jsonpath='https://{.spec.host}{"\n"}'
   ```

2. **Get Grafana credentials:**
   ```bash
   # Username
   oc get secret -n pelorus grafana-admin-credentials -o jsonpath='{.data.GF_SECURITY_ADMIN_USER}' | base64 -d
   
   # Password
   oc get secret -n pelorus grafana-admin-credentials -o jsonpath='{.data.GF_SECURITY_ADMIN_PASSWORD}' | base64 -d
   ```

### Viewing DORA Metrics

1. **Navigate to Pelorus Dashboards:**
   - Login to Grafana
   - Click hamburger menu → Dashboards → Browse
   - Open "pelorus" folder

2. **Key Dashboards:**
   - **Software Delivery Performance**: Overall DORA metrics
   - **Software Delivery Performance - By App**: Per-application metrics

3. **Filter for Your Application:**
   - Select "Software Delivery Performance - By App"
   - In "Application" dropdown, select "demo-app"
   - Adjust time range as needed

### Understanding the Metrics

- **Green metrics**: Meeting or exceeding targets
- **Yellow metrics**: Approaching threshold
- **Red metrics**: Below acceptable performance
- **N/A**: Insufficient data

## CI/CD Pipeline

### GitHub Actions Workflow

The pipeline (`.github/workflows/cicd.yml`) performs:

1. **Build and Push**:
   - Builds Docker image
   - Tags with commit SHA
   - Pushes to GitHub Container Registry

2. **Update Manifests**:
   - Updates image tag in Kustomization
   - Sets Pelorus annotations with:
     - Git commit SHA
     - Build timestamp
     - Build URL
     - Change ID

3. **Commit Changes**:
   - Commits updated manifests
   - Pushes to trigger ArgoCD sync

### Triggering Deployments

1. **Automatic deployments on push to main:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Manual sync via ArgoCD:**
   ```bash
   # Refresh application
   oc annotate application demo-app -n openshift-gitops \
     argocd.argoproj.io/refresh=hard --overwrite
   ```

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Not Syncing
```bash
# Check ArgoCD application status
oc get application demo-app -n openshift-gitops -o yaml | grep -A 10 status:

# Force sync
oc patch application demo-app -n openshift-gitops --type merge \
  -p '{"operation": {"initiatedBy": {"username": "admin"}, "sync": {"revision": "HEAD"}}}'
```

#### 2. Metrics Not Appearing in Grafana
```bash
# Check if Pelorus is monitoring your namespace
oc logs -n pelorus -l app.kubernetes.io/name=deploytime-exporter | grep pelorus-demo

# Verify annotations are present
oc get deployment demo-app -n pelorus-demo -o jsonpath='{.metadata.annotations}' | jq '.'

# Check Prometheus metrics
oc exec -n pelorus prometheus-prometheus-pelorus-0 -- \
  promtool query instant http://localhost:9090 'deploy_timestamp{namespace="pelorus-demo"}'
```

#### 3. Build Failures
```bash
# Check GitHub Actions logs
# Go to: https://github.com/<your-username>/gitops-demo-app/actions

# Verify GitHub secrets are configured for GHCR access
```

#### 4. Route Not Accessible
```bash
# Check route status
oc get route demo-app -n pelorus-demo

# Check pod logs
oc logs -n pelorus-demo deployment/demo-app
```

### Debugging Commands

```bash
# Check all resources in namespace
oc get all -n pelorus-demo

# Check ArgoCD sync status
oc get application demo-app -n openshift-gitops -o jsonpath='{.status.sync.status}'

# Check Pelorus exporter status
oc get pods -n pelorus | grep exporter

# View exporter metrics
oc exec -n pelorus $(oc get pod -n pelorus -l app.kubernetes.io/name=deploytime-exporter -o name) -- \
  curl -s localhost:8080/metrics | grep demo-app
```

## Repository Structure

```
gitops-demo-app/
├── .github/
│   └── workflows/
│       └── cicd.yml              # GitHub Actions workflow
├── app/
│   ├── app.py                    # Flask application
│   └── requirements.txt          # Python dependencies
├── argocd/
│   └── application.yaml          # ArgoCD Application definition
├── k8s/
│   ├── base/                     # Base Kubernetes manifests
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── route.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       └── prod/                 # Production overlay
│           ├── deployment-patch.yaml  # Pelorus annotations
│           ├── namespace.yaml
│           ├── rbac.yaml
│           └── kustomization.yaml
├── Dockerfile                    # Container image definition
└── README.md                     # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally using `kubectl kustomize k8s/overlays/prod`
5. Submit a pull request

## Advanced Configuration

### Custom Metrics Collection

To add custom metrics for your organization:

1. **Create custom annotations:**
   ```yaml
   metadata:
     annotations:
       company.io/team: "platform"
       company.io/cost-center: "engineering"
       company.io/environment: "production"
   ```

2. **Configure Pelorus to collect custom metrics:**
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: custom-metrics-config
     namespace: pelorus
   data:
     CUSTOM_LABELS: "company.io/team,company.io/environment"
   ```

### Multi-Environment Setup

To deploy to multiple environments:

1. **Create environment-specific overlays:**
   ```bash
   k8s/overlays/
   ├── dev/
   ├── staging/
   └── prod/
   ```

2. **Create separate ArgoCD applications:**
   ```bash
   argocd/
   ├── application-dev.yaml
   ├── application-staging.yaml
   └── application-prod.yaml
   ```

3. **Configure Pelorus to differentiate environments:**
   ```yaml
   metadata:
     labels:
       environment: "dev|staging|prod"
   ```

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review [Pelorus documentation](https://pelorus.readthedocs.io/)
3. Open an issue in this repository

## Acknowledgments

- Red Hat OpenShift for the container platform
- Pelorus project for DORA metrics implementation
- ArgoCD for GitOps capabilities
- Grafana for visualization